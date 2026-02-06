from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories.styles import (
    get_style,
    increment_style_views,
    list_styles_with_top_tattoo,
)
from core.repositories.tattoos import get_tattoo, list_tattoos_by_style
from core.services.menu import MENU_GALLERY

_PAGE_SIZE = 8
_MAX_PAGE = 200

_GALLERY_MESSAGE_ID_KEY = "gallery_message_id"


class GalleryCb(CallbackData, prefix="gallery"):
    action: str
    style_id: int | None = None
    tattoo_id: int | None = None
    page: int | None = None


def _styles_keyboard(styles: list[tuple[int, str, str | None]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for style_id, style_name, top_label in styles:
        text = style_name if top_label is None else f"{style_name} · {top_label}"
        builder.button(
            text=text,
            callback_data=GalleryCb(action="style", style_id=style_id, page=0).pack(),
        )
    builder.adjust(1)
    return builder.as_markup()


def _style_page_keyboard(
    *,
    style_id: int,
    page: int,
    tattoos: list[tuple[int, str, int]],
    has_prev: bool,
    has_next: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tattoo_id, name, views in tattoos:
        builder.button(
            text=f"{name} · {views}",
            callback_data=GalleryCb(
                action="tattoo", style_id=style_id, tattoo_id=tattoo_id, page=page
            ).pack(),
        )
    if has_prev:
        builder.button(
            text="« Назад",
            callback_data=GalleryCb(
                action="page", style_id=style_id, page=page - 1
            ).pack(),
        )
    if has_next:
        builder.button(
            text="Дальше »",
            callback_data=GalleryCb(
                action="page", style_id=style_id, page=page + 1
            ).pack(),
        )
    builder.button(text="К стилям", callback_data=GalleryCb(action="back").pack())

    # tattoos are 1-column; nav/back row is up to 3 buttons
    widths: list[int] = [1] * len(tattoos)
    widths.append(min(3, int(has_prev) + int(has_next) + 1))
    builder.adjust(*widths)
    return builder.as_markup()


def _tattoo_keyboard(*, style_id: int, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="← Назад",
        callback_data=GalleryCb(action="page", style_id=style_id, page=page).pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


async def _try_edit_message(
    *,
    message: Message,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None,
) -> bool:
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return True
        return False


async def _render_styles(
    *, session: AsyncSession
) -> tuple[str, InlineKeyboardMarkup | None]:
    rows = await list_styles_with_top_tattoo(session=session)
    styles: list[tuple[int, str, str | None]] = []
    for style, top in rows:
        top_label = None
        if top is not None:
            top_label = f"топ: {top.name} ({top.views})"
        styles.append((style.id, style.name, top_label))

    if not styles:
        return "Галерея пуста: стили не добавлены.", None

    return "Выберите стиль:", _styles_keyboard(styles)


async def _render_style_page(
    *,
    message: Message,
    session: AsyncSession,
    style_id: int,
    page: int,
) -> None:
    # Legacy helper left for compatibility; gallery flow now uses edit-only path.
    style = await get_style(session=session, style_id=style_id)
    if style is None:
        await message.answer("Стиль не найден.")
        return

    offset = page * _PAGE_SIZE
    items = await list_tattoos_by_style(
        session=session, style_id=style_id, limit=_PAGE_SIZE + 1, offset=offset
    )
    has_next = len(items) > _PAGE_SIZE
    items = items[:_PAGE_SIZE]
    has_prev = page > 0

    lines = [f"Стиль: {style.name}"]
    if not items:
        lines += ["", "Пока нет работ."]
    else:
        lines.append("")
        for i, t in enumerate(items, start=1 + offset):
            lines.append(f"{i}. {t.name} — {t.views} views")

    kb = _style_page_keyboard(
        style_id=style_id,
        page=page,
        tattoos=[(t.id, t.name, t.views) for t in items],
        has_prev=has_prev,
        has_next=has_next,
    )
    await message.answer("\n".join(lines), reply_markup=kb)


def create_gallery_router() -> Router:
    router = Router()

    @router.message(F.text == MENU_GALLERY)
    async def gallery_entry(
        message: Message, session: AsyncSession, state: FSMContext
    ) -> None:
        text, kb = await _render_styles(session=session)
        sent = await message.answer(text, reply_markup=kb)
        await state.update_data({_GALLERY_MESSAGE_ID_KEY: sent.message_id})

    @router.callback_query(GalleryCb.filter())
    async def gallery_callback(
        query: CallbackQuery,
        callback_data: GalleryCb,
        session: AsyncSession,
        state: FSMContext,
    ) -> None:
        if query.message is None:
            await query.answer()
            return

        data = await state.get_data()
        gallery_message_id = data.get(_GALLERY_MESSAGE_ID_KEY)
        if gallery_message_id is None:
            await query.answer(
                "Сессия завершена. Откройте «Галерея» заново.", show_alert=False
            )
            return
        if query.message.message_id != gallery_message_id:
            await query.answer("Сообщение устарело.", show_alert=False)
            return

        action = callback_data.action
        if action not in {"back", "style", "page", "tattoo"}:
            await query.answer("Некорректное действие.", show_alert=False)
            return

        if callback_data.action == "back":
            text, kb = await _render_styles(session=session)
            await _try_edit_message(
                message=query.message,
                message_id=int(gallery_message_id),
                text=text,
                reply_markup=kb,
            )
            await query.answer()
            return

        if callback_data.action == "style":
            if callback_data.style_id is None:
                await query.answer()
                return
            async with session.begin():
                await increment_style_views(
                    session=session,
                    style_id=callback_data.style_id,
                )

            page = 0
            offset = page * _PAGE_SIZE
            style = await get_style(session=session, style_id=callback_data.style_id)
            if style is None:
                await query.answer("Стиль не найден.", show_alert=False)
                return
            items = await list_tattoos_by_style(
                session=session,
                style_id=callback_data.style_id,
                limit=_PAGE_SIZE + 1,
                offset=offset,
            )
            has_next = len(items) > _PAGE_SIZE
            items = items[:_PAGE_SIZE]
            has_prev = False
            lines = [f"Стиль: {style.name}"]
            if not items:
                lines += ["", "Пока нет работ."]
            else:
                lines.append("")
                for i, t in enumerate(items, start=1 + offset):
                    lines.append(f"{i}. {t.name} — {t.views} views")
            kb = _style_page_keyboard(
                style_id=callback_data.style_id,
                page=page,
                tattoos=[(t.id, t.name, t.views) for t in items],
                has_prev=has_prev,
                has_next=has_next,
            )
            await _try_edit_message(
                message=query.message,
                message_id=int(gallery_message_id),
                text="\n".join(lines),
                reply_markup=kb,
            )
            await query.answer()
            return

        if callback_data.action == "page":
            if callback_data.style_id is None or callback_data.page is None:
                await query.answer()
                return
            page = max(0, min(_MAX_PAGE, int(callback_data.page)))
            offset = page * _PAGE_SIZE

            style = await get_style(session=session, style_id=callback_data.style_id)
            if style is None:
                await query.answer("Стиль не найден.", show_alert=False)
                return
            items = await list_tattoos_by_style(
                session=session,
                style_id=callback_data.style_id,
                limit=_PAGE_SIZE + 1,
                offset=offset,
            )
            has_next = len(items) > _PAGE_SIZE
            items = items[:_PAGE_SIZE]
            has_prev = page > 0
            lines = [f"Стиль: {style.name}"]
            if not items:
                lines += ["", "Пока нет работ."]
            else:
                lines.append("")
                for i, t in enumerate(items, start=1 + offset):
                    lines.append(f"{i}. {t.name} — {t.views} views")
            kb = _style_page_keyboard(
                style_id=callback_data.style_id,
                page=page,
                tattoos=[(t.id, t.name, t.views) for t in items],
                has_prev=has_prev,
                has_next=has_next,
            )
            await _try_edit_message(
                message=query.message,
                message_id=int(gallery_message_id),
                text="\n".join(lines),
                reply_markup=kb,
            )
            await query.answer()
            return

        if callback_data.action == "tattoo":
            if (
                callback_data.style_id is None
                or callback_data.tattoo_id is None
                or callback_data.page is None
            ):
                await query.answer()
                return

            tattoo = await get_tattoo(
                session=session, tattoo_id=callback_data.tattoo_id
            )
            if tattoo is None:
                await query.answer("Работа не найдена.", show_alert=False)
                await query.answer()
                return

            # Keep gallery edit-only (single message). Media edits are avoided here.
            text = (
                f"{tattoo.name}\n"
                f"views: {tattoo.views}\n"
                f"price: {tattoo.price or '—'}\n"
                f"photo: {'есть' if tattoo.photo_file_id else 'нет'}"
            )
            page = max(0, min(_MAX_PAGE, int(callback_data.page)))
            kb = _tattoo_keyboard(style_id=callback_data.style_id, page=page)
            await _try_edit_message(
                message=query.message,
                message_id=int(gallery_message_id),
                text=text,
                reply_markup=kb,
            )
            await query.answer()
            return

        await query.answer()

    return router


router = create_gallery_router()

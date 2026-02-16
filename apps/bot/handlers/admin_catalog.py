from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.states.admin_catalog import AdminCatalogStates
from core.config.settings import Settings
from core.repositories.styles import create_style, list_styles
from core.repositories.tattoos import create_tattoo


class AdminCatalogCb(CallbackData, prefix="admincat"):
    action: str
    style_id: int | None = None


def _ensure_admin(message: Message, settings: Settings) -> bool:
    user_id = message.from_user.id if message.from_user is not None else None
    return settings.is_admin_user(user_id)


def create_admin_catalog_router() -> Router:
    router = Router()

    @router.message(Command("add_style"))
    async def add_style_start(
        message: Message, state: FSMContext, settings: Settings
    ) -> None:
        if not _ensure_admin(message, settings):
            await message.answer("Недостаточно прав.")
            return
        await state.set_state(AdminCatalogStates.add_style_name)
        await message.answer("Введите название стиля:")

    @router.message(AdminCatalogStates.add_style_name)
    async def add_style_name(
        message: Message,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if not _ensure_admin(message, settings):
            await state.clear()
            await message.answer("Недостаточно прав.")
            return

        name = (message.text or "").strip()
        if not name:
            await message.answer("Введите название стиля текстом.")
            return

        try:
            async with session.begin():
                style = await create_style(session=session, name=name)
        except ValueError:
            await message.answer("Стиль уже существует.")
            return

        await state.clear()
        await message.answer(f"Стиль создан: {style.name} (id={style.id})")

    @router.message(Command("add_tattoo"))
    async def add_tattoo_start(
        message: Message,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if not _ensure_admin(message, settings):
            await message.answer("Недостаточно прав.")
            return

        styles = await list_styles(session=session)
        if not styles:
            await message.answer("Сначала добавьте стиль: /add_style")
            return

        builder = InlineKeyboardBuilder()
        for style in styles:
            builder.button(
                text=style.name,
                callback_data=AdminCatalogCb(action="style", style_id=style.id).pack(),
            )
        builder.adjust(1)

        await state.set_state(AdminCatalogStates.add_tattoo_style)
        await message.answer("Выберите стиль:", reply_markup=builder.as_markup())

    @router.callback_query(AdminCatalogCb.filter(), AdminCatalogStates.add_tattoo_style)
    async def add_tattoo_choose_style(
        query: CallbackQuery,
        callback_data: AdminCatalogCb,
        state: FSMContext,
        settings: Settings,
    ) -> None:
        if query.message is None:
            await query.answer()
            return

        user_id = query.from_user.id if query.from_user is not None else None
        if not settings.is_admin_user(user_id):
            await state.clear()
            await query.answer("Недостаточно прав.", show_alert=False)
            return

        if callback_data.action != "style" or callback_data.style_id is None:
            await query.answer()
            return

        await state.update_data({"style_id": callback_data.style_id})
        await state.set_state(AdminCatalogStates.add_tattoo_name)
        await query.message.answer("Введите название тату:")
        await query.answer()

    @router.message(AdminCatalogStates.add_tattoo_name)
    async def add_tattoo_name(
        message: Message, state: FSMContext, settings: Settings
    ) -> None:
        if not _ensure_admin(message, settings):
            await state.clear()
            await message.answer("Недостаточно прав.")
            return

        name = (message.text or "").strip()
        if not name:
            await message.answer("Введите название тату текстом.")
            return
        await state.update_data({"name": name})
        await state.set_state(AdminCatalogStates.add_tattoo_price)
        await message.answer("Введите цену числом или отправьте «-» чтобы пропустить:")

    @router.message(AdminCatalogStates.add_tattoo_price)
    async def add_tattoo_price(
        message: Message, state: FSMContext, settings: Settings
    ) -> None:
        if not _ensure_admin(message, settings):
            await state.clear()
            await message.answer("Недостаточно прав.")
            return

        raw = (message.text or "").strip()
        price: int | None
        if raw in {"-", "—"}:
            price = None
        else:
            try:
                price = int(raw)
            except ValueError:
                await message.answer("Цена должна быть числом или «-».")
                return
            if price < 0:
                await message.answer("Цена должна быть >= 0.")
                return

        await state.update_data({"price": price})
        await state.set_state(AdminCatalogStates.add_tattoo_photo)
        await message.answer("Отправьте фото тату или «-» чтобы пропустить:")

    @router.message(AdminCatalogStates.add_tattoo_photo)
    async def add_tattoo_photo(
        message: Message,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if not _ensure_admin(message, settings):
            await state.clear()
            await message.answer("Недостаточно прав.")
            return

        data = await state.get_data()
        style_id = data.get("style_id")
        name = data.get("name")
        price = data.get("price")
        if style_id is None or not name:
            await state.clear()
            await message.answer("Сессия прервана. Начните заново: /add_tattoo")
            return

        photo_file_id: str | None = None
        if message.photo:
            photo_file_id = message.photo[-1].file_id
        else:
            raw = (message.text or "").strip()
            if raw not in {"-", "—"}:
                await message.answer("Пришлите фото или «-».")
                return

        try:
            async with session.begin():
                tattoo = await create_tattoo(
                    session=session,
                    name=str(name),
                    style_id=int(style_id),
                    price=price if isinstance(price, int) else None,
                    photo_file_id=photo_file_id,
                )
        except ValueError:
            await message.answer("Тату с таким названием уже существует.")
            return

        await state.clear()
        await message.answer(f"Тату создано: {tattoo.name} (id={tattoo.id})")

    return router


router = create_admin_catalog_router()

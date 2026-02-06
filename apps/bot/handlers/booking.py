from __future__ import annotations

from datetime import date
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from apps.bot.states.booking import BookingStates
from core.config.settings import Settings
from core.services.booking_flow import (
    QUESTION_MESSAGE_ID_KEY,
    SUMMARY_MESSAGE_ID_KEY,
    BookingCb,
    build_summary_keyboard,
    next_missing_step,
    parse_set_value,
    question_for_step,
    render_summary,
)
from core.services.menu import MENU_BOOK, build_main_menu_keyboard

_EDIT_FIELDS = {
    "want_custom_sketch",
    "body_part",
    "calendar_date",
    "calendar_time",
    "promo_code",
}
_SET_FIELDS = {"want_custom_sketch", "body_part", "calendar_date"}
_SKIP_FIELDS = {"calendar_time", "promo_code"}


def _state_for_step(step: str) -> Any:
    mapping = {
        "want_custom_sketch": BookingStates.want_custom_sketch,
        "body_part": BookingStates.body_part,
        "calendar_date": BookingStates.calendar_date,
        "calendar_time": BookingStates.calendar_time,
        "promo_code": BookingStates.promo_code,
        "confirm": BookingStates.confirm,
    }
    return mapping[step]


async def _try_edit_message(
    *,
    message: Message,
    message_id: int,
    text: str,
    reply_markup: Any,
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
        # Common Telegram error when content is identical.
        if "message is not modified" in str(e).lower():
            return True
        return False


async def _try_delete_message(*, message: Message, message_id: int) -> bool:
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        return True
    except TelegramBadRequest:
        return False


async def _render_flow(*, message: Message, state: FSMContext, step: str) -> None:
    data = await state.get_data()

    summary_text = render_summary(data)
    summary_kb = build_summary_keyboard(data)
    question_text, question_kb = question_for_step(step, today=date.today())

    summary_id = data.get(SUMMARY_MESSAGE_ID_KEY)
    question_id = data.get(QUESTION_MESSAGE_ID_KEY)

    # Keep ordering invariant: summary must be "upper" message (older) than question.
    # If we can't edit both existing messages, we send a fresh pair in correct order.
    if summary_id is not None and question_id is not None:
        ok_summary = await _try_edit_message(
            message=message,
            message_id=summary_id,
            text=summary_text,
            reply_markup=summary_kb,
        )
        ok_question = await _try_edit_message(
            message=message,
            message_id=question_id,
            text=question_text,
            reply_markup=question_kb,
        )
        if ok_summary and ok_question:
            await state.set_state(_state_for_step(step))
            return

    # Best-effort cleanup: delete old bot messages (keep exactly 2 flow messages).
    if summary_id is not None:
        await _try_delete_message(message=message, message_id=summary_id)
    if question_id is not None:
        await _try_delete_message(message=message, message_id=question_id)

    sent_summary = await message.answer(summary_text, reply_markup=summary_kb)
    sent_question = await message.answer(question_text, reply_markup=question_kb)
    summary_id = sent_summary.message_id
    question_id = sent_question.message_id

    await state.update_data(
        {
            SUMMARY_MESSAGE_ID_KEY: summary_id,
            QUESTION_MESSAGE_ID_KEY: question_id,
        }
    )
    await state.set_state(_state_for_step(step))


async def _advance(*, message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step = next_missing_step(data)
    await _render_flow(message=message, state=state, step=step)


def create_booking_router() -> Router:
    router = Router()

    @router.message(F.text == MENU_BOOK)
    async def start_booking(message: Message, state: FSMContext) -> None:
        await _advance(message=message, state=state)

    @router.message(BookingStates.promo_code)
    async def promo_code_input(message: Message, state: FSMContext) -> None:
        code = (message.text or "").strip()
        # Treat empty input as "not answered yet": ask again.
        if not code:
            data = await state.get_data()
            question_id = data.get(QUESTION_MESSAGE_ID_KEY)
            if question_id is not None:
                await _try_edit_message(
                    message=message,
                    message_id=question_id,
                    text="Введите промокод или нажмите «Пропустить».",
                    reply_markup=question_for_step("promo_code", today=date.today())[1],
                )
            return

        await state.update_data({"promo_code": code})
        await _advance(message=message, state=state)

    @router.callback_query(BookingCb.filter())
    async def booking_callback(
        query: CallbackQuery,
        callback_data: BookingCb,
        state: FSMContext,
        settings: Settings,
    ) -> None:
        if query.message is None:
            await query.answer()
            return

        current_state = await state.get_state()
        data = await state.get_data()
        summary_id = data.get(SUMMARY_MESSAGE_ID_KEY)
        question_id = data.get(QUESTION_MESSAGE_ID_KEY)
        if current_state is None and callback_data.action != "confirm":
            await query.answer(
                "Сессия завершена. Нажмите «Записаться на сеанс» заново.",
                show_alert=False,
            )
            return
        if (
            summary_id is not None
            and question_id is not None
            and query.message.message_id not in {summary_id, question_id}
        ):
            await query.answer("Сообщение устарело.", show_alert=False)
            return

        if callback_data.action == "edit":
            step = callback_data.field
            if step is None or step not in _EDIT_FIELDS:
                await query.answer()
                return
            await _render_flow(message=query.message, state=state, step=step)
            await query.answer()
            return

        if callback_data.action == "skip":
            field = callback_data.field
            if field is None or field not in _SKIP_FIELDS:
                await query.answer()
                return
            await state.update_data({field: None})
            await _advance(message=query.message, state=state)
            await query.answer()
            return

        if callback_data.action == "set":
            field = callback_data.field
            value = callback_data.value
            if field is None or value is None or field not in _SET_FIELDS:
                await query.answer()
                return

            try:
                parsed = parse_set_value(field=field, value=value, today=date.today())
            except ValueError:
                await query.answer("Некорректное значение.", show_alert=False)
                return

            await state.update_data({field: parsed})
            await _advance(message=query.message, state=state)
            await query.answer()
            return

        if callback_data.action == "confirm":
            # Finish: disable old inline keyboards, clear draft, return to main menu.
            data = await state.get_data()
            summary_id = data.get(SUMMARY_MESSAGE_ID_KEY)
            question_id = data.get(QUESTION_MESSAGE_ID_KEY)

            if summary_id is not None:
                await _try_edit_message(
                    message=query.message,
                    message_id=summary_id,
                    text=f"{render_summary(data)}\n\nСтатус: подтверждено",
                    reply_markup=None,
                )
            if question_id is not None:
                await _try_edit_message(
                    message=query.message,
                    message_id=question_id,
                    text="Завершено.",
                    reply_markup=None,
                )

            await state.clear()
            is_admin = query.from_user.id in settings.admin_user_ids
            await query.message.answer(
                "Заявка подтверждена (заглушка). Главное меню:",
                reply_markup=build_main_menu_keyboard(is_admin=is_admin),
            )
            await query.answer()
            return

        await query.answer()

    return router


router = create_booking_router()

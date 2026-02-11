from __future__ import annotations

from datetime import date
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.states.booking import BookingStates
from core.config.settings import Settings
from core.services.booking_flow import (
    CONFIRM_IN_FLIGHT_KEY,
    ORDER_ID_KEY,
    QUESTION_MESSAGE_ID_KEY,
    SUMMARY_MESSAGE_ID_KEY,
    BookingCb,
    build_summary_keyboard,
    next_missing_step,
    parse_set_value,
    question_for_step,
    render_summary,
    reset_booking_draft_data,
)
from core.services.calendar_ui import CalendarCb, CalendarView, build_calendar_keyboard
from core.services.menu import MENU_BOOK, build_main_menu_keyboard
from core.services.schedule import DEFAULT_SCHEDULE_POLICY, today_msk

_EDIT_FIELDS = {
    "want_custom_sketch",
    "body_part",
    "calendar_date",
    "calendar_time",
    "promo_code",
}
_SET_FIELDS = {"want_custom_sketch", "body_part", "calendar_date", "calendar_time"}
_SKIP_FIELDS = {"promo_code"}


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


async def _send_main_menu(
    *,
    message: Message,
    settings: Settings,
    text: str = "Главное меню:",
) -> None:
    is_admin = message.from_user is not None and (
        message.from_user.id in settings.admin_user_ids
    )
    await message.answer(
        text,
        reply_markup=build_main_menu_keyboard(is_admin=is_admin),
    )


async def _replace_question_message(
    *,
    message: Message,
    state: FSMContext,
    text: str,
    reply_markup: Any,
) -> None:
    """
    Replace the "lower" question message if it can't be edited.
    Summary ordering invariant stays valid: summary is older than the new question.
    """
    data = await state.get_data()
    question_id = data.get(QUESTION_MESSAGE_ID_KEY)
    if question_id is not None:
        await _try_delete_message(message=message, message_id=question_id)
    sent = await message.answer(text, reply_markup=reply_markup)
    await state.update_data({QUESTION_MESSAGE_ID_KEY: sent.message_id})


async def _render_flow(*, message: Message, state: FSMContext, step: str) -> None:
    data = await state.get_data()

    summary_text = render_summary(data)
    summary_kb = build_summary_keyboard(data)
    question_text, question_kb = question_for_step(step, today=today_msk())

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
                ok = await _try_edit_message(
                    message=message,
                    message_id=question_id,
                    text="Введите промокод или нажмите «Пропустить».",
                    reply_markup=question_for_step("promo_code", today=today_msk())[1],
                )
                if not ok:
                    # Keep 2-message invariant and refresh message ids if needed.
                    await _render_flow(message=message, state=state, step="promo_code")
            return

        await state.update_data({"promo_code": code})
        await _advance(message=message, state=state)

    @router.callback_query(CalendarCb.filter())
    async def calendar_callback(
        query: CallbackQuery,
        callback_data: CalendarCb,
        state: FSMContext,
    ) -> None:
        if query.message is None:
            await query.answer()
            return

        current_state = await state.get_state()
        data = await state.get_data()
        summary_id = data.get(SUMMARY_MESSAGE_ID_KEY)
        question_id = data.get(QUESTION_MESSAGE_ID_KEY)
        today = today_msk()

        if current_state is None:
            await query.answer(
                "Сессия завершена. Нажмите «Записаться на сеанс» заново.",
                show_alert=False,
            )
            return

        # Calendar controls are only valid while choosing a date.
        if current_state != BookingStates.calendar_date.state:
            await query.answer("Сначала выберите шаг записи заново.", show_alert=False)
            return

        if (
            summary_id is not None
            and question_id is not None
            and query.message.message_id not in {summary_id, question_id}
        ):
            await query.answer("Сообщение устарело.", show_alert=False)
            return

        # Validate callback payload to avoid crashes on forged data.
        if not (1 <= callback_data.month <= 12):
            await query.answer("Некорректные данные.", show_alert=False)
            return
        from datetime import timedelta

        max_day = today + timedelta(days=DEFAULT_SCHEDULE_POLICY.days_ahead)
        if not (today.year - 1 <= callback_data.year <= max_day.year + 1):
            await query.answer("Некорректные данные.", show_alert=False)
            return
        # Keep navigation within allowed months window.
        min_view = (today.year, today.month)
        max_view = (max_day.year, max_day.month)
        if (callback_data.year, callback_data.month) < min_view or (
            callback_data.year,
            callback_data.month,
        ) > max_view:
            await query.answer("Некорректные данные.", show_alert=False)
            return

        if callback_data.action == "noop":
            await query.answer()
            return

        if callback_data.action in {"prev", "next"}:
            if question_id is None:
                await query.answer()
                return
            kb = build_calendar_keyboard(
                today=today,
                view=CalendarView(year=callback_data.year, month=callback_data.month),
                policy=DEFAULT_SCHEDULE_POLICY,
            )
            ok = await _try_edit_message(
                message=query.message,
                message_id=question_id,
                text="Выберите дату:",
                reply_markup=kb,
            )
            if not ok:
                # If the question message was deleted or can't be edited, replace it
                # and update FSM data.
                await _replace_question_message(
                    message=query.message,
                    state=state,
                    text="Выберите дату:",
                    reply_markup=kb,
                )
            await query.answer()
            return

        if callback_data.action == "day":
            if callback_data.day is None:
                await query.answer("Некорректная дата.", show_alert=False)
                return

            try:
                chosen = date(
                    callback_data.year, callback_data.month, callback_data.day
                )
            except ValueError:
                await query.answer("Некорректная дата.", show_alert=False)
                return
            from core.services.schedule import is_date_available

            if not is_date_available(
                chosen=chosen, today=today, policy=DEFAULT_SCHEDULE_POLICY
            ):
                await query.answer("Дата недоступна.", show_alert=False)
                return

            data["calendar_date"] = chosen.isoformat()
            data.pop("calendar_time", None)
            await state.set_data(data)
            await _advance(message=query.message, state=state)
            await query.answer()
            return

        await query.answer()

    @router.callback_query(BookingCb.filter())
    async def booking_callback(
        query: CallbackQuery,
        callback_data: BookingCb,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if query.message is None:
            await query.answer()
            return

        current_state = await state.get_state()
        data = await state.get_data()
        summary_id = data.get(SUMMARY_MESSAGE_ID_KEY)
        question_id = data.get(QUESTION_MESSAGE_ID_KEY)
        if current_state is None and callback_data.action not in {"confirm", "menu"}:
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
                parsed = parse_set_value(field=field, value=value, today=today_msk())
            except ValueError:
                await query.answer("Некорректное значение.", show_alert=False)
                return

            if field == "calendar_date":
                # If date is changed, time should be chosen again (remove the key).
                data = await state.get_data()
                data["calendar_date"] = parsed
                data.pop("calendar_time", None)
                await state.set_data(data)
            else:
                await state.update_data({field: parsed})
            await _advance(message=query.message, state=state)
            await query.answer()
            return

        if callback_data.action == "confirm":
            user = query.from_user
            if user is None:
                await query.answer(
                    "Не удалось определить пользователя.", show_alert=False
                )
                return

            data = await state.get_data()
            # Idempotency: if we already created an order for this draft,
            # do not create again.
            existing_order_id = data.get(ORDER_ID_KEY)
            if isinstance(existing_order_id, int) and existing_order_id > 0:
                order_id = existing_order_id
            else:
                if data.get(CONFIRM_IN_FLIGHT_KEY) is True:
                    await query.answer("Подтверждаем заявку...", show_alert=False)
                    return
                await state.update_data({CONFIRM_IN_FLIGHT_KEY: True})

            calendar_date = data.get("calendar_date")
            calendar_time = data.get("calendar_time")
            if not calendar_date or not calendar_time:
                await query.answer("Выберите дату и время.", show_alert=False)
                await state.update_data({CONFIRM_IN_FLIGHT_KEY: False})
                return

            from core.services.booking_orders import persist_booking_as_order

            nickname = (user.username or user.full_name or str(user.id))[:20]
            # Best-effort: disable inline keyboards ASAP to reduce
            # double-click duplicates.
            summary_id = data.get(SUMMARY_MESSAGE_ID_KEY)
            question_id = data.get(QUESTION_MESSAGE_ID_KEY)
            if summary_id is not None:
                await _try_edit_message(
                    message=query.message,
                    message_id=summary_id,
                    text=render_summary(data),
                    reply_markup=None,
                )
            if question_id is not None:
                # Keep text, just remove keyboard.
                question_text, _ = question_for_step("confirm", today=today_msk())
                await _try_edit_message(
                    message=query.message,
                    message_id=question_id,
                    text=question_text,
                    reply_markup=None,
                )

            if not (isinstance(existing_order_id, int) and existing_order_id > 0):
                try:
                    order_id = await persist_booking_as_order(
                        session=session,
                        tg_id=user.id,
                        tg_nickname=nickname,
                        calendar_date=str(calendar_date),
                        calendar_time=str(calendar_time),
                    )
                except Exception:
                    # Allow retry by restoring the confirm UI.
                    await state.update_data({CONFIRM_IN_FLIGHT_KEY: False})
                    await _render_flow(
                        message=query.message, state=state, step="confirm"
                    )
                    await query.answer(
                        "Не удалось подтвердить заявку. Попробуйте ещё раз.",
                        show_alert=False,
                    )
                    return
                await state.update_data({ORDER_ID_KEY: int(order_id)})

            # Finish: disable old inline keyboards, clear draft, return to main menu.
            if summary_id is not None:
                ok_s = await _try_edit_message(
                    message=query.message,
                    message_id=summary_id,
                    text=(
                        f"{render_summary(data)}\n\n"
                        f"Статус: подтверждено\n"
                        f"Заказ: #{order_id}"
                    ),
                    reply_markup=None,
                )
            else:
                ok_s = False
            if question_id is not None:
                ok_q = await _try_edit_message(
                    message=query.message,
                    message_id=question_id,
                    text=(
                        f"Заявка подтверждена. Номер заказа: #{order_id}\n\n"
                        "Главное меню доступно на клавиатуре ниже."
                    ),
                    reply_markup=None,
                )
            else:
                ok_q = False

            await state.clear()
            # Ensure user sees a result even if messages were deleted.
            if not (ok_s and ok_q):
                await _send_main_menu(
                    message=query.message,
                    settings=settings,
                    text=(
                        f"Заявка подтверждена. Номер заказа: #{order_id}\n\n"
                        "Главное меню:"
                    ),
                )
            await query.answer()
            return

        if callback_data.action == "reset":
            data = await state.get_data()
            await state.set_data(reset_booking_draft_data(data))
            await _render_flow(
                message=query.message, state=state, step="want_custom_sketch"
            )
            await query.answer()
            return

        if callback_data.action == "menu":
            data = await state.get_data()
            summary_id = data.get(SUMMARY_MESSAGE_ID_KEY)
            question_id = data.get(QUESTION_MESSAGE_ID_KEY)
            if summary_id is not None:
                await _try_delete_message(message=query.message, message_id=summary_id)
            if question_id is not None:
                await _try_delete_message(message=query.message, message_id=question_id)
            await state.clear()
            await _send_main_menu(message=query.message, settings=settings)
            await query.answer()
            return

        await query.answer()

    return router


router = create_booking_router()

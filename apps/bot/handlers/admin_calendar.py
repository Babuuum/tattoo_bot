from __future__ import annotations

from calendar import monthrange
from datetime import date, time

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.states.admin_calendar import AdminCalendarStates
from core.config.settings import Settings
from core.repositories import schedule_exceptions as exc_repo
from core.services.calendar_availability import _parse_time_hhmm
from core.services.calendar_ui import CalendarCb, CalendarView, build_calendar_keyboard
from core.services.menu import MENU_ADMIN
from core.services.schedule import DEFAULT_SCHEDULE_POLICY, list_time_slots, today_msk


class AdminCalCb(CallbackData, prefix="admincal"):
    action: str
    value: str | None = None


def _is_admin(*, user_id: int | None, settings: Settings) -> bool:
    return settings.is_admin_user(user_id)


def _append_back_button(
    kb: InlineKeyboardMarkup, *, text: str, cb: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            *kb.inline_keyboard,
            [InlineKeyboardButton(text=text, callback_data=cb)],
        ]
    )


async def _try_edit_markup(
    *, query: CallbackQuery, reply_markup: InlineKeyboardMarkup
) -> bool:
    if query.message is None:
        return False
    try:
        await query.message.edit_reply_markup(reply_markup=reply_markup)
        return True
    except TelegramBadRequest:
        return False


def _admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Выходной день", callback_data=AdminCalCb(action="dayoff").pack()
    )
    builder.button(text="Блок слота", callback_data=AdminCalCb(action="block").pack())
    builder.adjust(1)
    return builder.as_markup()


def _time_slots_kb(*, blocked: set[str] | None = None) -> InlineKeyboardMarkup:
    blocked = blocked or set()
    builder = InlineKeyboardBuilder()
    for slot in list_time_slots(DEFAULT_SCHEDULE_POLICY):
        label = f"{slot}x" if slot in blocked else slot
        builder.button(
            text=label,
            callback_data=AdminCalCb(action="toggle_slot", value=slot).pack(),
        )
    builder.adjust(3)
    return builder.as_markup()


def _month_bounds(view: CalendarView) -> tuple[date, date]:
    days_in_month = monthrange(view.year, view.month)[1]
    start = date(view.year, view.month, 1)
    end = date(view.year, view.month, days_in_month)
    return start, end


async def _dayoff_calendar_kb(
    *,
    session: AsyncSession,
    today: date,
    view: CalendarView,
) -> InlineKeyboardMarkup:
    start, end = _month_bounds(view)
    marked = await exc_repo.list_day_off_dates(
        session=session, start_date=start, end_date_inclusive=end
    )
    kb = build_calendar_keyboard(
        today=today,
        view=view,
        policy=DEFAULT_SCHEDULE_POLICY,
        marked_dates=marked,
    )
    return _append_back_button(kb, text="Назад", cb=AdminCalCb(action="back").pack())


async def _block_date_calendar_kb(
    *,
    today: date,
    view: CalendarView,
) -> InlineKeyboardMarkup:
    kb = build_calendar_keyboard(
        today=today,
        view=view,
        policy=DEFAULT_SCHEDULE_POLICY,
    )
    return _append_back_button(kb, text="Назад", cb=AdminCalCb(action="back").pack())


def create_admin_calendar_router() -> Router:
    router = Router()

    @router.message(F.text == MENU_ADMIN)
    async def admin_menu(
        message: Message, state: FSMContext, settings: Settings
    ) -> None:
        user_id = message.from_user.id if message.from_user is not None else None
        if not _is_admin(user_id=user_id, settings=settings):
            await message.answer("Недостаточно прав.")
            return
        await state.clear()
        await message.answer(
            "Админка: управление календарём", reply_markup=_admin_menu_kb()
        )

    @router.callback_query(AdminCalCb.filter(F.action == "dayoff"))
    async def dayoff_start(
        query: CallbackQuery,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if query.message is None:
            await query.answer()
            return
        user_id = query.from_user.id if query.from_user is not None else None
        if not _is_admin(user_id=user_id, settings=settings):
            await state.clear()
            await query.answer("Недостаточно прав.", show_alert=False)
            return

        today = today_msk()
        view = CalendarView(year=today.year, month=today.month)
        kb = await _dayoff_calendar_kb(session=session, today=today, view=view)
        await state.set_state(AdminCalendarStates.day_off_date)
        await query.message.answer("Выберите дату (toggle выходной):", reply_markup=kb)
        await query.answer()

    @router.callback_query(AdminCalCb.filter(F.action == "block"))
    async def block_start(
        query: CallbackQuery, state: FSMContext, settings: Settings
    ) -> None:
        if query.message is None:
            await query.answer()
            return
        user_id = query.from_user.id if query.from_user is not None else None
        if not _is_admin(user_id=user_id, settings=settings):
            await state.clear()
            await query.answer("Недостаточно прав.", show_alert=False)
            return

        today = today_msk()
        view = CalendarView(year=today.year, month=today.month)
        kb = await _block_date_calendar_kb(today=today, view=view)
        await state.set_state(AdminCalendarStates.block_date)
        await query.message.answer(
            "Выберите дату для блокировки слота:", reply_markup=kb
        )
        await query.answer()

    @router.callback_query(AdminCalCb.filter(F.action == "back"))
    async def admin_back(
        query: CallbackQuery, state: FSMContext, settings: Settings
    ) -> None:
        if query.message is None:
            await query.answer()
            return
        user_id = query.from_user.id if query.from_user is not None else None
        if not _is_admin(user_id=user_id, settings=settings):
            await state.clear()
            await query.answer("Недостаточно прав.", show_alert=False)
            return
        await state.clear()
        await query.message.answer(
            "Админка: управление календарём", reply_markup=_admin_menu_kb()
        )
        await query.answer()

    @router.callback_query(CalendarCb.filter(), AdminCalendarStates.day_off_date)
    async def dayoff_calendar_callback(
        query: CallbackQuery,
        callback_data: CalendarCb,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if query.message is None:
            await query.answer()
            return
        user_id = query.from_user.id if query.from_user is not None else None
        if not _is_admin(user_id=user_id, settings=settings):
            await state.clear()
            await query.answer("Недостаточно прав.", show_alert=False)
            return

        if callback_data.action in {"prev", "next"}:
            today = today_msk()
            kb = await _dayoff_calendar_kb(
                session=session,
                today=today,
                view=CalendarView(year=callback_data.year, month=callback_data.month),
            )
            await _try_edit_markup(query=query, reply_markup=kb)
            await query.answer()
            return
        if callback_data.action != "day" or callback_data.day is None:
            await query.answer()
            return

        try:
            chosen = date(callback_data.year, callback_data.month, callback_data.day)
        except ValueError:
            await query.answer("Некорректная дата.", show_alert=False)
            return

        async with session.begin():
            now_day_off = await exc_repo.toggle_day_off(session=session, day=chosen)

        # Refresh calendar markup to show updated markers.
        today = today_msk()
        kb = await _dayoff_calendar_kb(
            session=session,
            today=today,
            view=CalendarView(year=callback_data.year, month=callback_data.month),
        )
        await _try_edit_markup(query=query, reply_markup=kb)
        await query.answer(
            "Отмечено как выходной." if now_day_off else "Выходной снят.",
            show_alert=False,
        )

    @router.callback_query(CalendarCb.filter(), AdminCalendarStates.block_date)
    async def block_calendar_callback(
        query: CallbackQuery,
        callback_data: CalendarCb,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if query.message is None:
            await query.answer()
            return
        user_id = query.from_user.id if query.from_user is not None else None
        if not _is_admin(user_id=user_id, settings=settings):
            await state.clear()
            await query.answer("Недостаточно прав.", show_alert=False)
            return

        if callback_data.action in {"prev", "next"}:
            today = today_msk()
            kb = await _block_date_calendar_kb(
                today=today,
                view=CalendarView(year=callback_data.year, month=callback_data.month),
            )
            await _try_edit_markup(query=query, reply_markup=kb)
            await query.answer()
            return
        if callback_data.action != "day" or callback_data.day is None:
            await query.answer()
            return

        try:
            chosen = date(callback_data.year, callback_data.month, callback_data.day)
        except ValueError:
            await query.answer("Некорректная дата.", show_alert=False)
            return

        await state.update_data({"block_date": chosen.isoformat()})
        await state.set_state(AdminCalendarStates.block_time)
        blocked = await exc_repo.list_blocked_slots_for_date(
            session=session, day=chosen
        )
        blocked_hhmm = {f"{t.hour:02d}:{t.minute:02d}" for t in blocked}
        kb = _append_back_button(
            _time_slots_kb(blocked=blocked_hhmm),
            text="Назад",
            cb=AdminCalCb(action="back").pack(),
        )
        await query.message.answer(
            f"Дата: {chosen.isoformat()}\nВыберите слот (toggle):",
            reply_markup=kb,
        )
        await query.answer()

    @router.callback_query(
        AdminCalCb.filter(F.action == "toggle_slot"), AdminCalendarStates.block_time
    )
    async def toggle_slot(
        query: CallbackQuery,
        callback_data: AdminCalCb,
        state: FSMContext,
        settings: Settings,
        session: AsyncSession,
    ) -> None:
        if query.message is None:
            await query.answer()
            return
        user_id = query.from_user.id if query.from_user is not None else None
        if not _is_admin(user_id=user_id, settings=settings):
            await state.clear()
            await query.answer("Недостаточно прав.", show_alert=False)
            return

        slot = callback_data.value
        if not slot:
            await query.answer()
            return

        data = await state.get_data()
        raw_date = data.get("block_date")
        if not isinstance(raw_date, str):
            await state.clear()
            await query.answer(
                "Сессия устарела. Откройте «Админка» заново.", show_alert=False
            )
            return

        try:
            day = date.fromisoformat(raw_date)
            slot_time: time = _parse_time_hhmm(slot)
        except ValueError:
            await query.answer("Некорректные данные.", show_alert=False)
            return

        async with session.begin():
            now_blocked = await exc_repo.toggle_blocked_slot(
                session=session,
                day=day,
                slot_time=slot_time,
            )

        # Refresh keyboard so admin sees current blocked slots.
        blocked = await exc_repo.list_blocked_slots_for_date(session=session, day=day)
        blocked_hhmm = {f"{t.hour:02d}:{t.minute:02d}" for t in blocked}
        kb = _append_back_button(
            _time_slots_kb(blocked=blocked_hhmm),
            text="Назад",
            cb=AdminCalCb(action="back").pack(),
        )
        await _try_edit_markup(query=query, reply_markup=kb)
        await query.answer(
            "Слот заблокирован." if now_blocked else "Блокировка снята.",
            show_alert=False,
        )

    return router


router = create_admin_calendar_router()

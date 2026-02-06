from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.services.schedule import (
    DEFAULT_SCHEDULE_POLICY,
    SchedulePolicy,
    is_date_available,
)


class CalendarCb(CallbackData, prefix="cal"):
    action: str
    year: int
    month: int
    day: int | None = None


_WEEKDAYS_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


@dataclass(frozen=True, slots=True)
class CalendarView:
    year: int
    month: int


def _shift_month(view: CalendarView, delta: int) -> CalendarView:
    y, m = view.year, view.month
    m += delta
    while m <= 0:
        y -= 1
        m += 12
    while m > 12:
        y += 1
        m -= 12
    return CalendarView(year=y, month=m)


def build_calendar_keyboard(
    *,
    today: date,
    view: CalendarView,
    policy: SchedulePolicy = DEFAULT_SCHEDULE_POLICY,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Header
    builder.row(
        InlineKeyboardButton(
            text=f"{view.month:02d}.{view.year}",
            callback_data=CalendarCb(
                action="noop", year=view.year, month=view.month
            ).pack(),
        ),
    )

    # Weekdays
    builder.row(
        *[
            InlineKeyboardButton(
                text=wd,
                callback_data=CalendarCb(
                    action="noop", year=view.year, month=view.month
                ).pack(),
            )
            for wd in _WEEKDAYS_RU
        ],
        width=7,
    )

    # Days grid
    first_weekday, days_in_month = monthrange(view.year, view.month)  # Mon=0
    cells: list[tuple[str, str]] = []
    for _ in range(first_weekday):
        cells.append(
            (
                " ",
                CalendarCb(action="noop", year=view.year, month=view.month).pack(),
            )
        )

    for d in range(1, days_in_month + 1):
        chosen = date(view.year, view.month, d)
        selectable = is_date_available(chosen=chosen, today=today, policy=policy)
        text = f"{d}"
        if chosen == today:
            text = f"[{d}]"
        cells.append(
            (
                text,
                (
                    CalendarCb(
                        action="day", year=view.year, month=view.month, day=d
                    ).pack()
                    if selectable
                    else CalendarCb(
                        action="noop", year=view.year, month=view.month
                    ).pack()
                ),
            )
        )

    trailing = (7 - (len(cells) % 7)) % 7
    for _ in range(trailing):
        cells.append(
            (
                " ",
                CalendarCb(action="noop", year=view.year, month=view.month).pack(),
            )
        )

    for i in range(0, len(cells), 7):
        builder.row(
            *[
                InlineKeyboardButton(text=text, callback_data=cb)
                for text, cb in cells[i : i + 7]
            ],
            width=7,
        )

    # Navigation
    min_view = CalendarView(year=today.year, month=today.month)
    max_day = today + timedelta(days=policy.days_ahead)
    max_view = CalendarView(year=max_day.year, month=max_day.month)

    prev_view = _shift_month(view, -1)
    next_view = _shift_month(view, 1)

    builder.row(
        InlineKeyboardButton(
            text="«",
            callback_data=(
                CalendarCb(
                    action="prev", year=prev_view.year, month=prev_view.month
                ).pack()
                if (prev_view.year, prev_view.month) >= (min_view.year, min_view.month)
                else CalendarCb(action="noop", year=view.year, month=view.month).pack()
            ),
        ),
        InlineKeyboardButton(
            text="»",
            callback_data=(
                CalendarCb(
                    action="next", year=next_view.year, month=next_view.month
                ).pack()
                if (next_view.year, next_view.month) <= (max_view.year, max_view.month)
                else CalendarCb(action="noop", year=view.year, month=view.month).pack()
            ),
        ),
        width=2,
    )
    return builder.as_markup()

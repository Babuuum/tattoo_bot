from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.services.calendar_ui import CalendarView, build_calendar_keyboard
from core.services.schedule import DEFAULT_SCHEDULE_POLICY, list_time_slots

SUMMARY_MESSAGE_ID_KEY = "booking_summary_message_id"
QUESTION_MESSAGE_ID_KEY = "booking_question_message_id"


class BookingCb(CallbackData, prefix="booking"):
    action: str
    field: str | None = None
    value: str | None = None


@dataclass(frozen=True, slots=True)
class BookingField:
    key: str
    label: str


BOOKING_FIELDS: tuple[BookingField, ...] = (
    BookingField("want_custom_sketch", "Индивидуальный эскиз"),
    BookingField("body_part", "Часть тела"),
    BookingField("calendar_date", "Дата"),
    BookingField("calendar_time", "Время"),
    BookingField("promo_code", "Промокод"),
)


BODY_PART_OPTIONS: dict[str, str] = {
    "arm": "Рука",
    "leg": "Нога",
    "back": "Спина",
    "chest": "Грудь",
    "neck": "Шея",
    "other": "Другое",
}

EDITABLE_FIELD_KEYS: frozenset[str] = frozenset(field.key for field in BOOKING_FIELDS)


def is_answered(data: Mapping[str, Any], field: str) -> bool:
    # Important: False/None are valid answers; presence in FSM data is what matters.
    return field in data


def next_missing_step(data: Mapping[str, Any]) -> str:
    for field in BOOKING_FIELDS:
        if not is_answered(data, field.key):
            return field.key
    return "confirm"


def parse_set_value(*, field: str, value: str, today: date) -> Any:
    if field == "want_custom_sketch":
        if value not in {"0", "1"}:
            raise ValueError("Invalid want_custom_sketch")
        return value == "1"

    if field == "body_part":
        if value not in BODY_PART_OPTIONS:
            raise ValueError("Invalid body_part")
        return value

    if field == "calendar_date":
        try:
            chosen = date.fromisoformat(value)
        except ValueError as e:
            raise ValueError("Invalid calendar_date format") from e

        from core.services.schedule import is_date_available

        if not is_date_available(
            chosen=chosen, today=today, policy=DEFAULT_SCHEDULE_POLICY
        ):
            raise ValueError("calendar_date out of range")
        return value

    if field == "calendar_time":
        slots = set(list_time_slots(DEFAULT_SCHEDULE_POLICY))
        if value not in slots:
            raise ValueError("Invalid calendar_time")
        return value

    raise ValueError("Unsupported field for set")


def _fmt_value(field: str, value: Any) -> str:
    if value is None:
        return "Пропущено"
    if field == "want_custom_sketch":
        if value is True:
            return "Да"
        if value is False:
            return "Нет"
    if field == "body_part":
        return BODY_PART_OPTIONS.get(str(value), str(value))
    if field == "calendar_date":
        try:
            d = date.fromisoformat(str(value))
            return d.strftime("%d.%m.%Y")
        except ValueError:
            return str(value)
    return str(value)


def render_summary(data: Mapping[str, Any]) -> str:
    lines: list[str] = ["Сводка заказа", ""]
    for field in BOOKING_FIELDS:
        if is_answered(data, field.key):
            rendered = _fmt_value(field.key, data.get(field.key))
        else:
            rendered = "—"
        lines.append(f"{field.label}: {rendered}")
    return "\n".join(lines)


def build_summary_keyboard(data: Mapping[str, Any]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for field in BOOKING_FIELDS:
        if not is_answered(data, field.key):
            continue
        builder.button(
            text=f"Изменить: {field.label}",
            callback_data=BookingCb(action="edit", field=field.key).pack(),
        )
    builder.adjust(1)
    return builder.as_markup()


def build_want_custom_sketch_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да",
        callback_data=BookingCb(
            action="set", field="want_custom_sketch", value="1"
        ).pack(),
    )
    builder.button(
        text="Нет",
        callback_data=BookingCb(
            action="set", field="want_custom_sketch", value="0"
        ).pack(),
    )
    builder.adjust(2)
    return builder.as_markup()


def build_body_part_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in BODY_PART_OPTIONS.items():
        builder.button(
            text=label,
            callback_data=BookingCb(action="set", field="body_part", value=key).pack(),
        )
    builder.adjust(2)
    return builder.as_markup()


def build_calendar_date_keyboard(*, today: date) -> InlineKeyboardMarkup:
    return build_calendar_keyboard(
        today=today,
        view=CalendarView(year=today.year, month=today.month),
        policy=DEFAULT_SCHEDULE_POLICY,
    )


def build_calendar_time_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in list_time_slots(DEFAULT_SCHEDULE_POLICY):
        builder.button(
            text=slot,
            callback_data=BookingCb(
                action="set", field="calendar_time", value=slot
            ).pack(),
        )
    builder.adjust(3)
    return builder.as_markup()


def build_promo_code_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пропустить",
        callback_data=BookingCb(action="skip", field="promo_code").pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить", callback_data=BookingCb(action="confirm").pack())
    builder.adjust(1)
    return builder.as_markup()


def question_for_step(
    step: str, *, today: date
) -> tuple[str, InlineKeyboardMarkup | None]:
    if step == "want_custom_sketch":
        return "Нужен индивидуальный эскиз?", build_want_custom_sketch_keyboard()
    if step == "body_part":
        return "Выберите часть тела:", build_body_part_keyboard()
    if step == "calendar_date":
        return "Выберите дату:", build_calendar_date_keyboard(today=today)
    if step == "calendar_time":
        return "Выберите время (МСК):", build_calendar_time_keyboard()
    if step == "promo_code":
        return "Введите промокод или нажмите «Пропустить».", build_promo_code_keyboard()
    if step == "confirm":
        return "Проверьте сводку и подтвердите запись.", build_confirm_keyboard()
    raise ValueError(f"Unknown step: {step}")

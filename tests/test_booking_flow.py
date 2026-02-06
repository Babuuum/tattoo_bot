from __future__ import annotations

from datetime import date

from core.services.booking_flow import (
    build_summary_keyboard,
    next_missing_step,
    parse_set_value,
    render_summary,
)


def test_next_missing_step_empty() -> None:
    assert next_missing_step({}) == "want_custom_sketch"


def test_next_missing_step_skips_answered_false_and_none() -> None:
    data = {
        "want_custom_sketch": False,
        "body_part": "arm",
        "calendar_date": "2026-02-06",
    }
    assert next_missing_step(data) == "calendar_time"

    data["calendar_time"] = "12:00"
    assert next_missing_step(data) == "promo_code"

    data["promo_code"] = None
    assert next_missing_step(data) == "confirm"


def test_render_summary_renders_values_and_placeholders() -> None:
    text = render_summary(
        {
            "want_custom_sketch": False,
            "body_part": "arm",
            "promo_code": None,
        }
    )

    assert "Сводка заказа" in text
    assert "Индивидуальный эскиз: Нет" in text
    assert "Часть тела: Рука" in text
    assert "Дата: —" in text
    assert "Время: —" in text
    assert "Промокод: Пропущено" in text


def test_build_summary_keyboard_contains_edit_actions_for_answered_fields() -> None:
    kb = build_summary_keyboard(
        {
            "want_custom_sketch": True,
            "body_part": "arm",
            "calendar_time": None,
        }
    )

    buttons = [b for row in kb.inline_keyboard for b in row]
    assert [b.text for b in buttons] == [
        "Изменить: Индивидуальный эскиз",
        "Изменить: Часть тела",
        "Изменить: Время",
    ]
    assert [b.callback_data for b in buttons] == [
        "booking:edit:want_custom_sketch:",
        "booking:edit:body_part:",
        "booking:edit:calendar_time:",
    ]


def test_parse_set_value_validations() -> None:
    today = date(2026, 2, 6)

    assert parse_set_value(field="want_custom_sketch", value="1", today=today) is True
    assert parse_set_value(field="want_custom_sketch", value="0", today=today) is False
    assert parse_set_value(field="body_part", value="arm", today=today) == "arm"
    assert (
        parse_set_value(field="calendar_date", value="2026-02-06", today=today)
        == "2026-02-06"
    )
    assert parse_set_value(field="calendar_time", value="12:00", today=today) == "12:00"

    try:
        parse_set_value(field="body_part", value="bad", today=today)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    try:
        parse_set_value(field="calendar_date", value="2026-05-08", today=today)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    try:
        parse_set_value(field="calendar_time", value="11:00", today=today)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

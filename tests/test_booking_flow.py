from __future__ import annotations

from datetime import date

from core.services.booking_flow import (
    CONFIRM_IN_FLIGHT_KEY,
    ORDER_ID_KEY,
    QUESTION_MESSAGE_ID_KEY,
    SUMMARY_MESSAGE_ID_KEY,
    build_summary_keyboard,
    next_missing_step,
    parse_set_value,
    render_summary,
    reset_booking_draft_data,
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
        "Сбросить заявку",
        "В меню",
    ]
    callback_data = [b.callback_data for b in buttons]
    assert callback_data[0] == "booking:edit:want_custom_sketch:"
    assert callback_data[1] == "booking:edit:body_part:"
    assert callback_data[2] == "booking:edit:calendar_time:"
    assert callback_data[3].startswith("booking:reset")
    assert callback_data[4].startswith("booking:menu")


def test_reset_booking_draft_data_clears_fields_but_keeps_message_ids() -> None:
    data = {
        SUMMARY_MESSAGE_ID_KEY: 111,
        QUESTION_MESSAGE_ID_KEY: 222,
        CONFIRM_IN_FLIGHT_KEY: True,
        ORDER_ID_KEY: 999,
        "want_custom_sketch": True,
        "body_part": "arm",
        "calendar_date": "2026-02-06",
        "calendar_time": "12:00",
        "promo_code": "X",
        "price_estimate": 12345,
        "some_other_key": "keep",
    }

    new_data = reset_booking_draft_data(data)
    assert new_data[SUMMARY_MESSAGE_ID_KEY] == 111
    assert new_data[QUESTION_MESSAGE_ID_KEY] == 222
    assert new_data["some_other_key"] == "keep"

    assert "want_custom_sketch" not in new_data
    assert "body_part" not in new_data
    assert "calendar_date" not in new_data
    assert "calendar_time" not in new_data
    assert "promo_code" not in new_data
    assert "price_estimate" not in new_data
    assert CONFIRM_IN_FLIGHT_KEY not in new_data
    assert ORDER_ID_KEY not in new_data


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
    assert parse_set_value(field="calendar_time", value="1200", today=today) == "12:00"

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

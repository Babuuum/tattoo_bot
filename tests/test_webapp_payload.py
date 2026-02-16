from __future__ import annotations

import json

import pytest

from core.services.menu import MENU_TRYON, build_main_menu_keyboard
from core.services.webapp_payload import parse_web_app_data


def test_main_menu_tryon_button_has_webapp_url() -> None:
    kb = build_main_menu_keyboard(
        is_admin=False,
        mini_app_url="https://example.com/miniapp",
    )
    buttons = [button for row in kb.keyboard for button in row]
    tryon_button = next(button for button in buttons if button.text == MENU_TRYON)
    assert tryon_button.web_app is not None
    assert tryon_button.web_app.url == "https://example.com/miniapp"


def test_parse_web_app_data_ok() -> None:
    raw = json.dumps(
        {
            "price": 12000,
            "style_id": 2,
            "body_zone": "arm",
            "tattoo_id": 10,
            "promo_code": "PROMO10",
        }
    )
    data = parse_web_app_data(raw)

    assert data.price == 12000
    assert data.style_id == 2
    assert data.body_zone == "arm"
    assert data.tattoo_id == 10
    assert data.promo_code == "PROMO10"


@pytest.mark.parametrize(
    "payload, error",
    [
        ({"style_id": 1, "body_zone": "arm"}, "price must be int"),
        ({"price": "100", "style_id": 1, "body_zone": "arm"}, "price must be int"),
        ({"price": 100, "style_id": 0, "body_zone": "arm"}, "style_id must be >= 1"),
        (
            {"price": 100, "style_id": 1, "body_zone": ""},
            "body_zone must be non-empty string",
        ),
        (
            {"price": 100, "style_id": 1, "body_zone": "arm", "tattoo_id": "x"},
            "tattoo_id must be int",
        ),
    ],
)
def test_parse_web_app_data_invalid(payload: dict, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        parse_web_app_data(json.dumps(payload))

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class WebAppQuote:
    price: int
    style_id: int
    body_zone: str
    tattoo_id: int | None = None
    promo_code: str | None = None


def _as_int(*, payload: dict[str, Any], key: str, minimum: int) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be int")
    if value < minimum:
        raise ValueError(f"{key} must be >= {minimum}")
    return value


def _as_optional_int(*, payload: dict[str, Any], key: str, minimum: int) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"{key} must be int")
    if value < minimum:
        raise ValueError(f"{key} must be >= {minimum}")
    return value


def parse_web_app_data(raw: str) -> WebAppQuote:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError("invalid json") from e

    if not isinstance(payload, dict):
        raise ValueError("payload must be object")

    price = _as_int(payload=payload, key="price", minimum=0)
    style_id = _as_int(payload=payload, key="style_id", minimum=1)

    body_zone = payload.get("body_zone")
    if not isinstance(body_zone, str) or not body_zone.strip():
        raise ValueError("body_zone must be non-empty string")
    body_zone = body_zone.strip()[:50]

    tattoo_id = _as_optional_int(payload=payload, key="tattoo_id", minimum=1)

    promo_code = payload.get("promo_code")
    if promo_code is not None:
        if not isinstance(promo_code, str):
            raise ValueError("promo_code must be string")
        promo_code = promo_code.strip()[:50] or None

    return WebAppQuote(
        price=price,
        style_id=style_id,
        body_zone=body_zone,
        tattoo_id=tattoo_id,
        promo_code=promo_code,
    )


def render_quote_summary(quote: WebAppQuote) -> str:
    lines = [
        "Данные из Mini App получены.",
        "",
        f"Цена: {quote.price}",
        f"Стиль ID: {quote.style_id}",
        f"Зона: {quote.body_zone}",
    ]
    if quote.tattoo_id is not None:
        lines.append(f"Дизайн ID: {quote.tattoo_id}")
    if quote.promo_code:
        lines.append(f"Промокод: {quote.promo_code}")
    return "\n".join(lines)

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories import pricing as pricing_repo

_ONE = Decimal("1")
_TEN = Decimal("10")
_FIFTY = Decimal("50")
_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class PricingRequest:
    tg_id: int
    style_id: int
    body_zone: str
    promo_code: str | None = None


@dataclass(frozen=True, slots=True)
class PricingResult:
    pricing_config_id: int
    base_price: int
    min_price: int
    style_coefficient: Decimal
    body_zone_coefficient: Decimal
    raw_price: Decimal
    bounded_price: Decimal
    discount_multiplier: Decimal
    rounded_price: int
    rounding_policy: str


def _round_price(*, value: Decimal, policy: str) -> int:
    if policy == "round":
        return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if policy == "ceil":
        return int(value.quantize(Decimal("1"), rounding=ROUND_CEILING))
    if policy == "floor":
        return int(value.quantize(Decimal("1"), rounding=ROUND_FLOOR))
    if policy == "nearest_10":
        scaled = (value / _TEN).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(scaled * _TEN)
    if policy == "ceil_to_50":
        scaled = (value / _FIFTY).quantize(Decimal("1"), rounding=ROUND_CEILING)
        return int(scaled * _FIFTY)
    raise ValueError(f"unsupported rounding policy: {policy}")


def _as_positive_decimal(*, value: Decimal, field: str) -> Decimal:
    out = Decimal(value)
    if out <= _ZERO:
        raise ValueError(f"{field} must be > 0")
    return out


def _as_discount_multiplier(*, value: Decimal) -> Decimal:
    out = Decimal(value)
    if out <= _ZERO or out > _ONE:
        raise ValueError("discount multiplier must be in range (0, 1]")
    return out


async def _resolve_discount_multiplier(
    *,
    session: AsyncSession,
    tg_id: int,
    promo_code: str | None,
) -> Decimal:
    if promo_code:
        discount = await pricing_repo.get_active_discount_by_code(
            session=session, code=promo_code
        )
        if discount is not None and discount.multiplyer is not None:
            return _as_discount_multiplier(value=Decimal(discount.multiplyer))

    personal = await pricing_repo.get_user_personal_discount_multiplier(
        session=session, tg_id=tg_id
    )
    if personal is not None:
        return _as_discount_multiplier(value=Decimal(personal))

    return _ONE


async def calculate_price(
    *,
    session: AsyncSession,
    data: PricingRequest,
) -> PricingResult:
    config = await pricing_repo.get_active_pricing_config(session=session)
    if config is None:
        raise ValueError("active pricing config is not set")

    style_coeff = await pricing_repo.get_style_coefficient(
        session=session,
        pricing_config_id=config.id,
        style_id=data.style_id,
    )
    if style_coeff is None:
        raise ValueError("style coefficient is not configured")

    body_coeff = await pricing_repo.get_body_zone_coefficient(
        session=session,
        pricing_config_id=config.id,
        body_zone=data.body_zone,
    )
    if body_coeff is None:
        raise ValueError("body zone coefficient is not configured")

    base = _as_positive_decimal(value=Decimal(config.base_price), field="base_price")
    minimum = _as_positive_decimal(value=Decimal(config.min_price), field="min_price")

    style_multiplier = _as_positive_decimal(
        value=Decimal(style_coeff), field="style coefficient"
    )
    body_multiplier = _as_positive_decimal(
        value=Decimal(body_coeff), field="body zone coefficient"
    )

    raw_price = base * style_multiplier * body_multiplier
    bounded_price = max(minimum, raw_price)

    discount_multiplier = await _resolve_discount_multiplier(
        session=session,
        tg_id=data.tg_id,
        promo_code=data.promo_code,
    )
    discounted = bounded_price * discount_multiplier

    rounded = _round_price(value=discounted, policy=config.rounding_policy)
    if rounded < 0:
        rounded = 0

    return PricingResult(
        pricing_config_id=config.id,
        base_price=config.base_price,
        min_price=config.min_price,
        style_coefficient=style_multiplier,
        body_zone_coefficient=body_multiplier,
        raw_price=raw_price,
        bounded_price=bounded_price,
        discount_multiplier=discount_multiplier,
        rounded_price=rounded,
        rounding_policy=config.rounding_policy,
    )

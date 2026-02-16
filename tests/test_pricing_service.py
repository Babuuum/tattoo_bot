from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from core.services.pricing_service import PricingRequest, calculate_price


@pytest.mark.asyncio
async def test_calculate_price_requires_active_config(monkeypatch) -> None:
    async def _none(**_kwargs):
        return None

    monkeypatch.setattr("core.repositories.pricing.get_active_pricing_config", _none)

    with pytest.raises(ValueError, match="active pricing config is not set"):
        await calculate_price(
            session=None,
            data=PricingRequest(tg_id=1, style_id=1, body_zone="arm", promo_code=None),
        )


@pytest.mark.asyncio
async def test_calculate_price_applies_min_price_and_round(monkeypatch) -> None:
    async def _config(**_kwargs):
        return SimpleNamespace(
            id=1,
            base_price=1000,
            min_price=2000,
            rounding_policy="round",
        )

    async def _style(**_kwargs):
        return Decimal("1.10")

    async def _body(**_kwargs):
        return Decimal("1.20")

    async def _discount(**_kwargs):
        return None

    async def _personal(**_kwargs):
        return None

    monkeypatch.setattr("core.repositories.pricing.get_active_pricing_config", _config)
    monkeypatch.setattr("core.repositories.pricing.get_style_coefficient", _style)
    monkeypatch.setattr("core.repositories.pricing.get_body_zone_coefficient", _body)
    monkeypatch.setattr(
        "core.repositories.pricing.get_active_discount_by_code", _discount
    )
    monkeypatch.setattr(
        "core.repositories.pricing.get_user_personal_discount_multiplier", _personal
    )

    result = await calculate_price(
        session=None,
        data=PricingRequest(tg_id=1, style_id=1, body_zone="arm", promo_code=None),
    )

    assert result.raw_price == Decimal("1320.00")
    assert result.bounded_price == Decimal("2000")
    assert result.rounded_price == 2000


@pytest.mark.asyncio
async def test_calculate_price_applies_promo_and_ceil_to_50(monkeypatch) -> None:
    async def _config(**_kwargs):
        return SimpleNamespace(
            id=7,
            base_price=1000,
            min_price=500,
            rounding_policy="ceil_to_50",
        )

    async def _style(**_kwargs):
        return Decimal("1.20")

    async def _body(**_kwargs):
        return Decimal("1.10")

    async def _discount(**_kwargs):
        return SimpleNamespace(multiplyer=Decimal("0.90"))

    async def _personal(**_kwargs):
        return Decimal("0.50")

    monkeypatch.setattr("core.repositories.pricing.get_active_pricing_config", _config)
    monkeypatch.setattr("core.repositories.pricing.get_style_coefficient", _style)
    monkeypatch.setattr("core.repositories.pricing.get_body_zone_coefficient", _body)
    monkeypatch.setattr(
        "core.repositories.pricing.get_active_discount_by_code", _discount
    )
    monkeypatch.setattr(
        "core.repositories.pricing.get_user_personal_discount_multiplier", _personal
    )

    result = await calculate_price(
        session=None,
        data=PricingRequest(tg_id=1, style_id=2, body_zone="arm", promo_code="PROMO"),
    )

    assert result.discount_multiplier == Decimal("0.90")
    assert result.rounded_price == 1200


@pytest.mark.asyncio
async def test_calculate_price_applies_personal_discount_when_promo_missing(
    monkeypatch,
) -> None:
    async def _config(**_kwargs):
        return SimpleNamespace(
            id=2,
            base_price=1000,
            min_price=500,
            rounding_policy="nearest_10",
        )

    async def _style(**_kwargs):
        return Decimal("1.00")

    async def _body(**_kwargs):
        return Decimal("1.00")

    async def _discount(**_kwargs):
        return None

    async def _personal(**_kwargs):
        return Decimal("0.93")

    monkeypatch.setattr("core.repositories.pricing.get_active_pricing_config", _config)
    monkeypatch.setattr("core.repositories.pricing.get_style_coefficient", _style)
    monkeypatch.setattr("core.repositories.pricing.get_body_zone_coefficient", _body)
    monkeypatch.setattr(
        "core.repositories.pricing.get_active_discount_by_code", _discount
    )
    monkeypatch.setattr(
        "core.repositories.pricing.get_user_personal_discount_multiplier", _personal
    )

    result = await calculate_price(
        session=None,
        data=PricingRequest(tg_id=1, style_id=2, body_zone="arm", promo_code=None),
    )

    assert result.discount_multiplier == Decimal("0.93")
    assert result.rounded_price == 930


@pytest.mark.asyncio
async def test_calculate_price_rejects_invalid_discount_multiplier(monkeypatch) -> None:
    async def _config(**_kwargs):
        return SimpleNamespace(
            id=2,
            base_price=1000,
            min_price=500,
            rounding_policy="round",
        )

    async def _style(**_kwargs):
        return Decimal("1.00")

    async def _body(**_kwargs):
        return Decimal("1.00")

    async def _discount(**_kwargs):
        return SimpleNamespace(multiplyer=Decimal("-0.50"))

    async def _personal(**_kwargs):
        return None

    monkeypatch.setattr("core.repositories.pricing.get_active_pricing_config", _config)
    monkeypatch.setattr("core.repositories.pricing.get_style_coefficient", _style)
    monkeypatch.setattr("core.repositories.pricing.get_body_zone_coefficient", _body)
    monkeypatch.setattr(
        "core.repositories.pricing.get_active_discount_by_code", _discount
    )
    monkeypatch.setattr(
        "core.repositories.pricing.get_user_personal_discount_multiplier", _personal
    )

    with pytest.raises(ValueError, match="discount multiplier must be in range"):
        await calculate_price(
            session=None,
            data=PricingRequest(
                tg_id=1, style_id=2, body_zone="arm", promo_code="PROMO"
            ),
        )


@pytest.mark.asyncio
async def test_calculate_price_rejects_non_positive_coefficients(monkeypatch) -> None:
    async def _config(**_kwargs):
        return SimpleNamespace(
            id=2,
            base_price=1000,
            min_price=500,
            rounding_policy="round",
        )

    async def _style(**_kwargs):
        return Decimal("0")

    async def _body(**_kwargs):
        return Decimal("1.00")

    async def _discount(**_kwargs):
        return None

    async def _personal(**_kwargs):
        return None

    monkeypatch.setattr("core.repositories.pricing.get_active_pricing_config", _config)
    monkeypatch.setattr("core.repositories.pricing.get_style_coefficient", _style)
    monkeypatch.setattr("core.repositories.pricing.get_body_zone_coefficient", _body)
    monkeypatch.setattr(
        "core.repositories.pricing.get_active_discount_by_code", _discount
    )
    monkeypatch.setattr(
        "core.repositories.pricing.get_user_personal_discount_multiplier", _personal
    )

    with pytest.raises(ValueError, match="style coefficient must be > 0"):
        await calculate_price(
            session=None,
            data=PricingRequest(tg_id=1, style_id=2, body_zone="arm", promo_code=None),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rounding_policy, expected_price",
    [
        ("ceil", 1000),
        ("floor", 999),
    ],
)
async def test_calculate_price_rounding_policies(
    monkeypatch, rounding_policy: str, expected_price: int
) -> None:
    async def _config(**_kwargs):
        return SimpleNamespace(
            id=3,
            base_price=999,
            min_price=1,
            rounding_policy=rounding_policy,
        )

    async def _style(**_kwargs):
        return Decimal("1.001")

    async def _body(**_kwargs):
        return Decimal("1.000")

    async def _discount(**_kwargs):
        return None

    async def _personal(**_kwargs):
        return None

    monkeypatch.setattr("core.repositories.pricing.get_active_pricing_config", _config)
    monkeypatch.setattr("core.repositories.pricing.get_style_coefficient", _style)
    monkeypatch.setattr("core.repositories.pricing.get_body_zone_coefficient", _body)
    monkeypatch.setattr(
        "core.repositories.pricing.get_active_discount_by_code", _discount
    )
    monkeypatch.setattr(
        "core.repositories.pricing.get_user_personal_discount_multiplier", _personal
    )

    result = await calculate_price(
        session=None,
        data=PricingRequest(tg_id=1, style_id=2, body_zone="arm", promo_code=None),
    )

    assert result.rounded_price == expected_price

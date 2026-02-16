from __future__ import annotations

from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models.discount import Discount
from infra.db.models.pricing_body_zone_coefficient import PricingBodyZoneCoefficient
from infra.db.models.pricing_config import PricingConfig
from infra.db.models.pricing_style_coefficient import PricingStyleCoefficient
from infra.db.models.user import User


async def get_active_pricing_config(*, session: AsyncSession) -> PricingConfig | None:
    result = await session.execute(
        select(PricingConfig)
        .where(PricingConfig.active.is_(True))
        .order_by(desc(PricingConfig.updated_at), desc(PricingConfig.id))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_style_coefficient(
    *,
    session: AsyncSession,
    pricing_config_id: int,
    style_id: int,
) -> Decimal | None:
    result = await session.execute(
        select(PricingStyleCoefficient.coefficient)
        .where(PricingStyleCoefficient.pricing_config_id == pricing_config_id)
        .where(PricingStyleCoefficient.style_id == style_id)
    )
    return result.scalar_one_or_none()


async def get_body_zone_coefficient(
    *,
    session: AsyncSession,
    pricing_config_id: int,
    body_zone: str,
) -> Decimal | None:
    result = await session.execute(
        select(PricingBodyZoneCoefficient.coefficient)
        .where(PricingBodyZoneCoefficient.pricing_config_id == pricing_config_id)
        .where(PricingBodyZoneCoefficient.body_zone == body_zone)
    )
    return result.scalar_one_or_none()


async def get_active_discount_by_code(
    *, session: AsyncSession, code: str
) -> Discount | None:
    result = await session.execute(
        select(Discount)
        .where(Discount.active.is_(True))
        .where(Discount.code == code)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_user_personal_discount_multiplier(
    *, session: AsyncSession, tg_id: int
) -> Decimal | None:
    result = await session.execute(
        select(User.persanal_discount).where(User.tg_id == tg_id).limit(1)
    )
    return result.scalar_one_or_none()

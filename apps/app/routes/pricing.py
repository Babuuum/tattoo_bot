from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.app.routes.deps import get_session, get_webapp_identity
from apps.app.schemas.webapp import PricingCalcRequest, PricingCalcResponse
from core.services.pricing_service import PricingRequest, calculate_price
from core.services.webapp_auth_service import WebAppIdentity

router = APIRouter(prefix="/api/pricing", tags=["pricing"])
logger = logging.getLogger(__name__)


@router.post("/calc", response_model=PricingCalcResponse)
async def pricing_calc(
    payload: PricingCalcRequest,
    identity: Annotated[WebAppIdentity, Depends(get_webapp_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PricingCalcResponse:
    logger.info(
        "Pricing calculation requested",
        extra={
            "tg_id": identity.tg_id,
            "style_id": payload.style_id,
            "body_zone": payload.body_zone,
            "has_promo_code": bool(payload.promo_code),
        },
    )
    try:
        result = await calculate_price(
            session=session,
            data=PricingRequest(
                tg_id=identity.tg_id,
                style_id=payload.style_id,
                body_zone=payload.body_zone,
                promo_code=payload.promo_code,
            ),
        )
    except ValueError as e:
        logger.warning(
            "Pricing calculation rejected",
            extra={"tg_id": identity.tg_id, "reason": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e)) from e

    logger.info(
        "Pricing calculation success",
        extra={
            "tg_id": identity.tg_id,
            "final_price": result.rounded_price,
            "pricing_config_id": result.pricing_config_id,
        },
    )
    return PricingCalcResponse(
        pricing_config_id=result.pricing_config_id,
        base_price=result.base_price,
        min_price=result.min_price,
        style_coefficient=result.style_coefficient,
        body_zone_coefficient=result.body_zone_coefficient,
        raw_price=result.raw_price,
        bounded_price=result.bounded_price,
        discount_multiplier=result.discount_multiplier,
        final_price=result.rounded_price,
        rounding_policy=result.rounding_policy,
    )

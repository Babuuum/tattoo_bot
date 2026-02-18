from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from apps.app.routes.deps import (
    enforce_webapp_auth_rate_limit,
    get_redis,
    get_session,
    get_settings,
    get_webapp_identity,
)
from apps.app.schemas.webapp import (
    SelectedDesignRequest,
    SelectedDesignResponse,
    WebAppAuthRequest,
    WebAppAuthResponse,
    WebAppContextResponse,
    WebAppUser,
)
from core.config.settings import Settings
from core.repositories.tattoos import get_tattoo
from core.services.webapp_auth_service import WebAppIdentity, authenticate_webapp
from core.services.webapp_context_service import (
    build_webapp_context,
    set_selected_design,
)

router = APIRouter(prefix="/api/webapp", tags=["webapp"])
logger = logging.getLogger(__name__)


@router.post("/auth", response_model=WebAppAuthResponse)
async def webapp_auth(
    payload: WebAppAuthRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis)],
    _rate_limit: Annotated[None, Depends(enforce_webapp_auth_rate_limit)],
) -> WebAppAuthResponse:
    logger.info("WebApp auth attempt")
    try:
        result = await authenticate_webapp(
            settings=settings,
            redis=redis,
            init_data=payload.init_data,
            dev_shared_secret=payload.dev_shared_secret,
        )
    except ValueError as e:
        logger.warning("WebApp auth rejected")
        # Avoid exposing auth internals (signature age / replay) in API response.
        raise HTTPException(status_code=401, detail="Unauthorized") from e

    logger.info("WebApp auth success", extra={"tg_id": result.identity.tg_id})
    return WebAppAuthResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
        user=WebAppUser(tg_id=result.identity.tg_id, username=result.identity.username),
    )


@router.get("/context", response_model=WebAppContextResponse)
async def webapp_context(
    identity: Annotated[WebAppIdentity, Depends(get_webapp_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> WebAppContextResponse:
    logger.info("WebApp context requested", extra={"tg_id": identity.tg_id})
    context = await build_webapp_context(
        session=session,
        redis=redis,
        identity=identity,
    )
    return WebAppContextResponse(
        user=WebAppUser(tg_id=context.tg_id, username=context.username),
        selected_design_id=context.selected_design_id,
        selected_design_name=context.selected_design_name,
        pricing_config_id=context.pricing_config_id,
    )


@router.post("/selected-design", response_model=SelectedDesignResponse)
async def webapp_selected_design(
    payload: SelectedDesignRequest,
    identity: Annotated[WebAppIdentity, Depends(get_webapp_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> SelectedDesignResponse:
    logger.info(
        "WebApp selected design update requested",
        extra={"tg_id": identity.tg_id, "tattoo_id": payload.tattoo_id},
    )
    tattoo = await get_tattoo(session=session, tattoo_id=payload.tattoo_id)
    if tattoo is None:
        logger.warning(
            "WebApp selected design not found",
            extra={"tg_id": identity.tg_id, "tattoo_id": payload.tattoo_id},
        )
        raise HTTPException(status_code=404, detail="Tattoo not found")

    await set_selected_design(
        redis=redis,
        tg_id=identity.tg_id,
        tattoo_id=payload.tattoo_id,
    )
    logger.info(
        "WebApp selected design updated",
        extra={"tg_id": identity.tg_id, "tattoo_id": payload.tattoo_id},
    )
    return SelectedDesignResponse(ok=True, selected_design_id=payload.tattoo_id)

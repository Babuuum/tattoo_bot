from __future__ import annotations

from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories.pricing import get_active_pricing_config
from core.repositories.tattoos import get_tattoo
from core.services.webapp_auth_service import WebAppIdentity

_SELECTED_DESIGN_TEMPLATE = "user:{tg_id}:selected_design_id"


@dataclass(frozen=True, slots=True)
class WebAppContext:
    tg_id: int
    username: str | None
    selected_design_id: int | None
    selected_design_name: str | None
    pricing_config_id: int | None


def selected_design_key(*, tg_id: int) -> str:
    return _SELECTED_DESIGN_TEMPLATE.format(tg_id=tg_id)


async def set_selected_design(*, redis: Redis, tg_id: int, tattoo_id: int) -> None:
    key = selected_design_key(tg_id=tg_id)
    await redis.set(key, str(tattoo_id))


async def get_selected_design_id(*, redis: Redis, tg_id: int) -> int | None:
    key = selected_design_key(tg_id=tg_id)
    raw = await redis.get(key)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


async def build_webapp_context(
    *,
    session: AsyncSession,
    redis: Redis,
    identity: WebAppIdentity,
) -> WebAppContext:
    selected_design_id = await get_selected_design_id(redis=redis, tg_id=identity.tg_id)
    selected_design_name: str | None = None
    if selected_design_id is not None:
        tattoo = await get_tattoo(session=session, tattoo_id=selected_design_id)
        if tattoo is None:
            selected_design_id = None
        else:
            selected_design_name = tattoo.name

    config = await get_active_pricing_config(session=session)
    pricing_config_id = config.id if config is not None else None

    return WebAppContext(
        tg_id=identity.tg_id,
        username=identity.username,
        selected_design_id=selected_design_id,
        selected_design_name=selected_design_name,
        pricing_config_id=pricing_config_id,
    )

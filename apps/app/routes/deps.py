from __future__ import annotations

import logging
import re
import time
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.settings import Settings
from core.services.webapp_auth_service import WebAppIdentity, get_identity_by_token

bearer_scheme = HTTPBearer(auto_error=False)
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{20,200}$")
logger = logging.getLogger(__name__)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_maker: async_sessionmaker[AsyncSession] = request.app.state.session_maker
    async with session_maker() as session:
        yield session


async def get_webapp_identity(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    redis: Annotated[Redis, Depends(get_redis)],
) -> WebAppIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        logger.warning("Missing or invalid bearer auth scheme for WebApp endpoint")
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = credentials.credentials
    if not _TOKEN_RE.fullmatch(token):
        logger.warning("Malformed bearer token format for WebApp endpoint")
        raise HTTPException(status_code=401, detail="Unauthorized")

    identity = await get_identity_by_token(redis=redis, token=token)
    if identity is None:
        logger.warning("Unknown or expired bearer token for WebApp endpoint")
        raise HTTPException(status_code=401, detail="Unauthorized")

    return identity


async def enforce_webapp_auth_rate_limit(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    client_ip = request.client.host if request.client is not None else "unknown"
    bucket = int(time.time() // 60)
    key = f"rl:webapp_auth:{client_ip}:{bucket}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 90)
    if count > settings.webapp_auth_rate_limit_per_minute:
        logger.warning(
            "WebApp auth rate limit exceeded",
            extra={"client_ip": client_ip, "count": count},
        )
        raise HTTPException(status_code=429, detail="Too Many Requests")

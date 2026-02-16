from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from redis.asyncio import Redis

from core.config.settings import Settings

_AUTH_TOKEN_PREFIX = "webapp:auth:"
_REPLAY_PREFIX = "webapp:replay:"


@dataclass(frozen=True, slots=True)
class WebAppIdentity:
    tg_id: int
    username: str | None


@dataclass(frozen=True, slots=True)
class WebAppAuthResult:
    access_token: str
    expires_in: int
    identity: WebAppIdentity


def _data_check_string(items: dict[str, str]) -> str:
    chunks = [f"{k}={v}" for k, v in sorted(items.items())]
    return "\n".join(chunks)


def _derive_webapp_secret(bot_token: str) -> bytes:
    return hmac.new(
        key=b"WebAppData", msg=bot_token.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()


def validate_telegram_init_data(
    *, init_data: str, bot_token: str, max_age_seconds: int, now_ts: int | None = None
) -> WebAppIdentity:
    pairs = parse_qsl(init_data, keep_blank_values=True)
    if not pairs:
        raise ValueError("initData is empty")

    data: dict[str, str] = {}
    for key, value in pairs:
        if key in data:
            raise ValueError(f"duplicate initData key: {key}")
        data[key] = value
    hash_value = data.pop("hash", "")
    if not hash_value:
        raise ValueError("initData hash is missing")

    secret = _derive_webapp_secret(bot_token)
    check_string = _data_check_string(data)
    computed_hash = hmac.new(
        key=secret,
        msg=check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(computed_hash, hash_value):
        raise ValueError("invalid initData signature")

    raw_auth_date = data.get("auth_date")
    if raw_auth_date is None:
        raise ValueError("auth_date is missing")

    try:
        auth_date = int(raw_auth_date)
    except ValueError as e:
        raise ValueError("invalid auth_date") from e

    now = now_ts if now_ts is not None else int(time.time())
    if auth_date > now + 30:
        raise ValueError("auth_date is in the future")
    if now - auth_date > max_age_seconds:
        raise ValueError("initData is too old")

    raw_user = data.get("user")
    if not raw_user:
        raise ValueError("user is missing")

    try:
        user_data = json.loads(raw_user)
    except json.JSONDecodeError as e:
        raise ValueError("invalid user payload") from e

    tg_id = user_data.get("id")
    if not isinstance(tg_id, int):
        raise ValueError("invalid user id")

    username = user_data.get("username")
    if username is not None and not isinstance(username, str):
        username = None

    return WebAppIdentity(tg_id=tg_id, username=username)


def _build_dev_identity() -> WebAppIdentity:
    # Keep dev sessions isolated between different local clients.
    tg_id = -secrets.randbelow(2_000_000_000) - 1
    return WebAppIdentity(tg_id=tg_id, username="dev")


async def _store_auth_session(
    *,
    redis: Redis,
    identity: WebAppIdentity,
    expires_in: int,
) -> WebAppAuthResult:
    token = secrets.token_urlsafe(32)
    payload = {
        "tg_id": identity.tg_id,
        "username": identity.username,
    }
    key = f"{_AUTH_TOKEN_PREFIX}{token}"
    await redis.set(key, json.dumps(payload), ex=expires_in)
    return WebAppAuthResult(
        access_token=token, expires_in=expires_in, identity=identity
    )


async def _claim_init_data_once(
    *,
    redis: Redis,
    init_data: str,
    ttl_seconds: int,
) -> bool:
    digest = hashlib.sha256(init_data.encode("utf-8")).hexdigest()
    key = f"{_REPLAY_PREFIX}{digest}"
    claimed = await redis.set(key, "1", ex=ttl_seconds, nx=True)
    return bool(claimed)


async def authenticate_webapp(
    *,
    settings: Settings,
    redis: Redis,
    init_data: str | None,
    dev_shared_secret: str | None,
) -> WebAppAuthResult:
    if settings.app_env == "prod":
        if not init_data:
            raise ValueError("initData is required in prod")
        identity = validate_telegram_init_data(
            init_data=init_data,
            bot_token=settings.bot_token,
            max_age_seconds=settings.webapp_auth_max_age_seconds,
        )
        if not await _claim_init_data_once(
            redis=redis,
            init_data=init_data,
            ttl_seconds=settings.webapp_auth_max_age_seconds,
        ):
            raise ValueError("replay detected")
        return await _store_auth_session(
            redis=redis,
            identity=identity,
            expires_in=settings.webapp_auth_max_age_seconds,
        )

    if init_data:
        identity = validate_telegram_init_data(
            init_data=init_data,
            bot_token=settings.bot_token,
            max_age_seconds=settings.webapp_auth_max_age_seconds,
        )
        if not await _claim_init_data_once(
            redis=redis,
            init_data=init_data,
            ttl_seconds=settings.webapp_auth_max_age_seconds,
        ):
            raise ValueError("replay detected")
        return await _store_auth_session(
            redis=redis,
            identity=identity,
            expires_in=settings.webapp_auth_max_age_seconds,
        )

    if dev_shared_secret and settings.dev_shared_secret:
        if hmac.compare_digest(dev_shared_secret, settings.dev_shared_secret):
            return await _store_auth_session(
                redis=redis,
                identity=_build_dev_identity(),
                expires_in=settings.webapp_auth_max_age_seconds,
            )

    raise ValueError("invalid credentials")


async def get_identity_by_token(*, redis: Redis, token: str) -> WebAppIdentity | None:
    key = f"{_AUTH_TOKEN_PREFIX}{token}"
    raw = await redis.get(key)
    if raw is None:
        return None

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None

    tg_id = payload.get("tg_id")
    username = payload.get("username")
    if not isinstance(tg_id, int):
        return None
    if username is not None and not isinstance(username, str):
        username = None
    return WebAppIdentity(tg_id=tg_id, username=username)

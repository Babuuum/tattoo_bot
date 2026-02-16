from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from core.config.settings import Settings
from core.services.webapp_auth_service import (
    authenticate_webapp,
    validate_telegram_init_data,
)


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool:
        if nx and key in self._store:
            return False
        self._store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)


def _build_settings(monkeypatch, *, app_env: str, dev_secret: str = "") -> Settings:
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("ADMIN_USER_IDS", "123")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.com")
    monkeypatch.setenv("WEBHOOK_PATH", "/tg/webhook")
    monkeypatch.setenv("WEBHOOK_SECRET_TOKEN", "secret")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("DB_NAME", "app")
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "postgres")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("WEBAPP_AUTH_MAX_AGE_SECONDS", "300")
    monkeypatch.setenv("DEV_SHARED_SECRET", dev_secret)
    return Settings()


def _build_init_data(*, bot_token: str, auth_date: int) -> str:
    user_payload = json.dumps({"id": 1001, "username": "tester"}, separators=(",", ":"))
    data = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": user_payload,
    }
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    hash_value = hmac.new(secret, check.encode("utf-8"), hashlib.sha256).hexdigest()
    payload = {**data, "hash": hash_value}
    return urlencode(payload)


def test_validate_telegram_init_data_rejects_invalid_hash(monkeypatch) -> None:
    settings = _build_settings(monkeypatch, app_env="prod")
    init_data = _build_init_data(
        bot_token=settings.bot_token, auth_date=int(time.time())
    )
    bad_data = init_data.replace("hash=", "hash=deadbeef", 1)

    with pytest.raises(ValueError, match="invalid initData signature"):
        validate_telegram_init_data(
            init_data=bad_data,
            bot_token=settings.bot_token,
            max_age_seconds=settings.webapp_auth_max_age_seconds,
        )


@pytest.mark.asyncio
async def test_dev_secret_works_only_in_dev(monkeypatch) -> None:
    redis = FakeRedis()

    dev_settings = _build_settings(monkeypatch, app_env="dev", dev_secret="shared")
    dev_result = await authenticate_webapp(
        settings=dev_settings,
        redis=redis,
        init_data=None,
        dev_shared_secret="shared",
    )
    assert dev_result.identity.tg_id < 0

    prod_settings = _build_settings(monkeypatch, app_env="prod", dev_secret="shared")
    with pytest.raises(ValueError, match="initData is required in prod"):
        await authenticate_webapp(
            settings=prod_settings,
            redis=redis,
            init_data=None,
            dev_shared_secret="shared",
        )


def test_validate_telegram_init_data_rejects_duplicate_keys(monkeypatch) -> None:
    settings = _build_settings(monkeypatch, app_env="prod")
    init_data = _build_init_data(
        bot_token=settings.bot_token, auth_date=int(time.time())
    )
    bad_data = f"{init_data}&auth_date=1"

    with pytest.raises(ValueError, match="duplicate initData key"):
        validate_telegram_init_data(
            init_data=bad_data,
            bot_token=settings.bot_token,
            max_age_seconds=settings.webapp_auth_max_age_seconds,
        )


def test_validate_telegram_init_data_rejects_too_old_auth_date(monkeypatch) -> None:
    settings = _build_settings(monkeypatch, app_env="prod")
    init_data = _build_init_data(
        bot_token=settings.bot_token,
        auth_date=int(time.time()) - 301,
    )

    with pytest.raises(ValueError, match="initData is too old"):
        validate_telegram_init_data(
            init_data=init_data,
            bot_token=settings.bot_token,
            max_age_seconds=300,
        )


@pytest.mark.asyncio
async def test_authenticate_webapp_rejects_replay(monkeypatch) -> None:
    redis = FakeRedis()
    settings = _build_settings(monkeypatch, app_env="prod")
    init_data = _build_init_data(
        bot_token=settings.bot_token, auth_date=int(time.time())
    )

    await authenticate_webapp(
        settings=settings,
        redis=redis,
        init_data=init_data,
        dev_shared_secret=None,
    )
    with pytest.raises(ValueError, match="replay detected"):
        await authenticate_webapp(
            settings=settings,
            redis=redis,
            init_data=init_data,
            dev_shared_secret=None,
        )

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock

from aiogram import Dispatcher
from fastapi.testclient import TestClient


class DummySession:
    async def close(self) -> None:
        return None


class DummyBot:
    def __init__(self) -> None:
        self.session = DummySession()
        self.set_webhook = AsyncMock()
        self.delete_webhook = AsyncMock()


class FakeRedis:
    def __init__(self) -> None:
        self._values: dict[str, int | str] = {}

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool:
        if nx and key in self._values:
            return False
        self._values[key] = value
        return True

    async def get(self, key: str) -> str | None:
        value = self._values.get(key)
        return value if isinstance(value, str) else None

    async def incr(self, key: str) -> int:
        value = self._values.get(key)
        if value is None:
            current = 0
        elif isinstance(value, int):
            current = value
        else:
            current = int(value)
        current += 1
        self._values[key] = current
        return current

    async def expire(self, key: str, seconds: int) -> bool:
        return key in self._values and seconds > 0

    async def close(self) -> None:
        return None


def _set_env(monkeypatch, *, app_env: str, rate_limit: int) -> None:
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("MINI_APP_URL", "https://example.com/miniapp")
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
    monkeypatch.setenv("WEBAPP_AUTH_RATE_LIMIT_PER_MINUTE", str(rate_limit))
    monkeypatch.setenv("DEV_SHARED_SECRET", "shared")


def _build_app(monkeypatch, *, app_env: str, rate_limit: int):
    _set_env(monkeypatch, app_env=app_env, rate_limit=rate_limit)
    module = importlib.import_module("apps.app.main")

    dummy_bot = DummyBot()
    dispatcher = Dispatcher()
    dispatcher.feed_update = AsyncMock()

    fake_redis = FakeRedis()

    monkeypatch.setattr(module, "create_bot", lambda _settings: dummy_bot)
    monkeypatch.setattr(module, "create_dispatcher", lambda **_kwargs: dispatcher)
    monkeypatch.setattr(module, "create_redis", lambda _url: fake_redis)

    async def fake_start_polling(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(module, "start_polling", fake_start_polling)

    app = module.create_app()
    return app


def test_webapp_auth_does_not_leak_internal_errors(monkeypatch) -> None:
    app = _build_app(monkeypatch, app_env="prod", rate_limit=20)
    client = TestClient(app)

    response = client.post("/api/webapp/auth", json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_webapp_auth_rate_limit(monkeypatch) -> None:
    app = _build_app(monkeypatch, app_env="dev", rate_limit=1)
    client = TestClient(app)

    first = client.post("/api/webapp/auth", json={"dev_shared_secret": "shared"})
    second = client.post("/api/webapp/auth", json={"dev_shared_secret": "shared"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json() == {"detail": "Too Many Requests"}

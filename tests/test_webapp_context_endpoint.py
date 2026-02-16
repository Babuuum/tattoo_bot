from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram import Dispatcher
from fastapi.testclient import TestClient

from apps.app.routes import deps as deps_module
from core.services.webapp_auth_service import WebAppIdentity
from core.services.webapp_context_service import selected_design_key


class DummySession:
    async def close(self) -> None:
        return None


class DummyBot:
    def __init__(self) -> None:
        self.session = DummySession()
        self.set_webhook = AsyncMock()
        self.delete_webhook = AsyncMock()


class FakeRedis:
    def __init__(self, data: dict[str, str] | None = None) -> None:
        self._store = data or {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value


def _set_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
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


def _build_app(monkeypatch):
    _set_env(monkeypatch)
    module = importlib.import_module("apps.app.main")

    dummy_bot = DummyBot()
    dispatcher = Dispatcher()
    dispatcher.feed_update = AsyncMock()

    monkeypatch.setattr(module, "create_bot", lambda _settings: dummy_bot)
    monkeypatch.setattr(module, "create_dispatcher", lambda **_kwargs: dispatcher)

    async def fake_start_polling(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(module, "start_polling", fake_start_polling)

    return module.create_app()


def test_webapp_context_contract_with_selected_design(monkeypatch) -> None:
    app = _build_app(monkeypatch)

    fake_redis = FakeRedis({selected_design_key(tg_id=42): "10"})

    async def _identity_override() -> WebAppIdentity:
        return WebAppIdentity(tg_id=42, username="tester")

    async def _session_override():
        yield object()

    def _redis_override() -> FakeRedis:
        return fake_redis

    async def _get_tattoo(**_kwargs):
        return SimpleNamespace(name="Dragon")

    async def _get_active_config(**_kwargs):
        return SimpleNamespace(id=5)

    monkeypatch.setattr("core.services.webapp_context_service.get_tattoo", _get_tattoo)
    monkeypatch.setattr(
        "core.services.webapp_context_service.get_active_pricing_config",
        _get_active_config,
    )

    app.dependency_overrides[deps_module.get_webapp_identity] = _identity_override
    app.dependency_overrides[deps_module.get_session] = _session_override
    app.dependency_overrides[deps_module.get_redis] = _redis_override

    client = TestClient(app)
    response = client.get("/api/webapp/context")

    assert response.status_code == 200
    assert response.json() == {
        "user": {"tg_id": 42, "username": "tester"},
        "selected_design_id": 10,
        "selected_design_name": "Dragon",
        "pricing_config_id": 5,
    }


def test_webapp_context_handles_invalid_selected_design_value(monkeypatch) -> None:
    app = _build_app(monkeypatch)

    fake_redis = FakeRedis({selected_design_key(tg_id=7): "not-an-int"})

    async def _identity_override() -> WebAppIdentity:
        return WebAppIdentity(tg_id=7, username="u7")

    async def _session_override():
        yield object()

    def _redis_override() -> FakeRedis:
        return fake_redis

    async def _get_tattoo(**_kwargs):
        raise AssertionError(
            "get_tattoo should not be called for invalid selected_design"
        )

    async def _get_active_config(**_kwargs):
        return None

    monkeypatch.setattr("core.services.webapp_context_service.get_tattoo", _get_tattoo)
    monkeypatch.setattr(
        "core.services.webapp_context_service.get_active_pricing_config",
        _get_active_config,
    )

    app.dependency_overrides[deps_module.get_webapp_identity] = _identity_override
    app.dependency_overrides[deps_module.get_session] = _session_override
    app.dependency_overrides[deps_module.get_redis] = _redis_override

    client = TestClient(app)
    response = client.get("/api/webapp/context")

    assert response.status_code == 200
    assert response.json() == {
        "user": {"tg_id": 7, "username": "u7"},
        "selected_design_id": None,
        "selected_design_name": None,
        "pricing_config_id": None,
    }

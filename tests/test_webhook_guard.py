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


def _set_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
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


def _minimal_update_payload() -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 1, "type": "private"},
        },
    }


def _build_app(monkeypatch):
    _set_env(monkeypatch)
    module = importlib.import_module("apps.app.main")

    dummy_bot = DummyBot()
    dispatcher = Dispatcher()
    dispatcher.feed_update = AsyncMock()

    monkeypatch.setattr(module, "create_bot", lambda _settings: dummy_bot)
    monkeypatch.setattr(module, "create_dispatcher", lambda **_kwargs: dispatcher)

    app = module.create_app()
    return app, dispatcher


def test_webhook_guard_403(monkeypatch) -> None:
    app, _dispatcher = _build_app(monkeypatch)
    client = TestClient(app)

    response = client.post(
        "/tg/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        json=_minimal_update_payload(),
    )

    assert response.status_code == 403


def test_webhook_guard_ok(monkeypatch) -> None:
    app, dispatcher = _build_app(monkeypatch)
    client = TestClient(app)

    response = client.post(
        "/tg/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "secret"},
        json=_minimal_update_payload(),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert dispatcher.feed_update.called

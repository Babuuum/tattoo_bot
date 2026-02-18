from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def _set_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
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


def _build_client(monkeypatch) -> TestClient:
    _set_env(monkeypatch)
    module = importlib.import_module("apps.app.main")

    async def fake_start_polling(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(module, "start_polling", fake_start_polling)

    return TestClient(module.create_app())


def test_miniapp_endpoint_returns_html(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/miniapp")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!doctype html>" in response.text.lower()


def test_miniapp_model_asset_is_available(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/assets/models/m_std.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_miniapp_tattoo_asset_is_available(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/assets/tattoos/rose.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0

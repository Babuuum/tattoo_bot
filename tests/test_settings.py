from __future__ import annotations

from core.config.settings import Settings


def test_settings_parsing(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("ADMIN_USER_IDS", "123, 456")
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
    monkeypatch.setenv("MINI_APP_URL", "https://prod.example/miniapp")
    monkeypatch.setenv("MINI_APP_DEV_URL", "http://localhost:5173/miniapp")
    monkeypatch.setenv("DEV_ALLOW_ALL_ADMINS", "true")

    settings = Settings()

    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"
    assert settings.admin_user_ids == [123, 456]
    assert settings.api_port == 8000
    assert settings.resolved_mini_app_url == "http://localhost:5173/miniapp"
    assert settings.is_admin_user(999) is True
    assert (
        settings.database_url
        == "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    )


def test_settings_admin_gate_in_prod(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("ADMIN_USER_IDS", "123, 456")
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
    monkeypatch.setenv("MINI_APP_URL", "https://prod.example/miniapp")
    monkeypatch.setenv("MINI_APP_DEV_URL", "http://localhost:5173/miniapp")
    monkeypatch.setenv("DEV_ALLOW_ALL_ADMINS", "true")

    settings = Settings()

    assert settings.resolved_mini_app_url == "https://prod.example/miniapp"
    assert settings.is_admin_user(123) is True
    assert settings.is_admin_user(999) is False

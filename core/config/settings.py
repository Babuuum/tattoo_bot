from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_parse_delimiter=",",
    )

    app_env: Literal["dev", "prod"] = Field("dev", validation_alias="APP_ENV")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    bot_token: str = Field(..., validation_alias="BOT_TOKEN")
    mini_app_url: str = Field(
        "https://example.com/miniapp",
        validation_alias="MINI_APP_URL",
    )
    admin_user_ids: Annotated[list[int], NoDecode] = Field(
        default_factory=list, validation_alias="ADMIN_USER_IDS"
    )

    webhook_url: str = Field("", validation_alias="WEBHOOK_URL")
    webhook_path: str = Field("/tg/webhook", validation_alias="WEBHOOK_PATH")
    webhook_secret_token: str = Field("", validation_alias="WEBHOOK_SECRET_TOKEN")

    api_host: str = Field("0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(8000, validation_alias="API_PORT")

    db_name: str = Field(..., validation_alias="DB_NAME")
    db_user: str = Field(..., validation_alias="DB_USER")
    db_password: str = Field(..., validation_alias="DB_PASSWORD")
    db_host: str = Field(..., validation_alias="DB_HOST")
    db_port: int = Field(5432, validation_alias="DB_PORT")
    redis_url: str = Field(..., validation_alias="REDIS_URL")
    webapp_auth_max_age_seconds: int = Field(
        300, validation_alias="WEBAPP_AUTH_MAX_AGE_SECONDS"
    )
    webapp_auth_rate_limit_per_minute: int = Field(
        20, validation_alias="WEBAPP_AUTH_RATE_LIMIT_PER_MINUTE"
    )
    dev_shared_secret: str = Field("", validation_alias="DEV_SHARED_SECRET")

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def parse_admin_user_ids(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list):
            return value
        if value is None:
            return []
        items = [item.strip() for item in str(value).split(",") if item.strip()]
        return [int(item) for item in items]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

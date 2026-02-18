from __future__ import annotations

import re
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
    mini_app_dev_url: str = Field(
        "http://127.0.0.1:3000/miniapp",
        validation_alias="MINI_APP_DEV_URL",
    )
    dev_allow_all_admins: bool = Field(
        True,
        validation_alias="DEV_ALLOW_ALL_ADMINS",
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
        items = [
            item.strip() for item in re.split(r"[,\s;]+", str(value)) if item.strip()
        ]
        return [int(item) for item in items]

    def is_admin_user(self, user_id: int | None) -> bool:
        if user_id is None:
            return False
        if self.app_env == "dev" and self.dev_allow_all_admins:
            return True
        return user_id in self.admin_user_ids

    @property
    def resolved_mini_app_url(self) -> str:
        if self.app_env == "dev":
            return self.mini_app_dev_url
        return self.mini_app_url

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

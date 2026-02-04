from __future__ import annotations

from enum import Enum
from typing import Literal


class BotMode(str, Enum):
    POLLING = "polling"
    WEBHOOK = "webhook"


def get_bot_mode(app_env: Literal["dev", "prod"]) -> BotMode:
    if app_env == "prod":
        return BotMode.WEBHOOK
    return BotMode.POLLING

from __future__ import annotations

from core.services.mode import BotMode, get_bot_mode


def test_bot_mode_dev() -> None:
    assert get_bot_mode("dev") == BotMode.POLLING


def test_bot_mode_prod() -> None:
    assert get_bot_mode("prod") == BotMode.WEBHOOK

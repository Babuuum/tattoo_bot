from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from core.services.schedule import today_msk


def test_today_msk_matches_moscow_date() -> None:
    expected = datetime.now(ZoneInfo("Europe/Moscow")).date()
    assert today_msk() == expected

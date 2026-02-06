from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")
UTC_TZ = UTC


@dataclass(frozen=True, slots=True)
class SchedulePolicy:
    days_ahead: int
    start_hour: int
    end_hour_inclusive: int


DEFAULT_SCHEDULE_POLICY = SchedulePolicy(
    days_ahead=90,
    start_hour=12,
    end_hour_inclusive=20,
)


def today_msk() -> date:
    # Booking UI and availability rules are Moscow-time based.
    return datetime.now(MOSCOW_TZ).date()


def is_date_available(*, chosen: date, today: date, policy: SchedulePolicy) -> bool:
    min_d = today
    max_d = today + timedelta(days=policy.days_ahead)
    return min_d <= chosen <= max_d


def list_time_slots(policy: SchedulePolicy) -> list[str]:
    return [
        f"{hour:02d}:00"
        for hour in range(policy.start_hour, policy.end_hour_inclusive + 1)
    ]


def compose_start_at_utc(*, chosen_date: date, chosen_time: time) -> datetime:
    dt_msk = datetime(
        chosen_date.year,
        chosen_date.month,
        chosen_date.day,
        chosen_time.hour,
        chosen_time.minute,
        tzinfo=MOSCOW_TZ,
    )
    return dt_msk.astimezone(UTC_TZ)

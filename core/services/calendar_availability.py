from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories import orders as orders_repo
from core.repositories import schedule_exceptions as exc_repo
from core.services.schedule import (
    DEFAULT_SCHEDULE_POLICY,
    MOSCOW_TZ,
    SchedulePolicy,
    compose_start_at_utc,
    list_time_slots,
)


def _time_to_hhmm(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"


def _parse_time_hhmm(value: str) -> time:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("invalid time format")
    h, m = int(parts[0]), int(parts[1])
    return time(hour=h, minute=m)


def _msk_day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    start = compose_start_at_utc(chosen_date=day, chosen_time=time(0, 0))
    end = compose_start_at_utc(
        chosen_date=day + timedelta(days=1), chosen_time=time(0, 0)
    )
    return start, end


def _compute_available_slots(
    *,
    policy: SchedulePolicy,
    is_day_off: bool,
    blocked: Iterable[str],
    booked: Iterable[str],
) -> list[str]:
    if is_day_off:
        return []
    blocked_set = set(blocked)
    booked_set = set(booked)
    all_slots = list_time_slots(policy)
    return [s for s in all_slots if s not in blocked_set and s not in booked_set]


@dataclass(frozen=True, slots=True)
class CalendarAvailabilityService:
    policy: SchedulePolicy = DEFAULT_SCHEDULE_POLICY

    async def get_available_slots(
        self,
        *,
        session: AsyncSession,
        day: date,
    ) -> list[str]:
        if await exc_repo.is_day_off(session=session, day=day):
            return []

        blocked_times = await exc_repo.list_blocked_slots_for_date(
            session=session, day=day
        )
        blocked = {_time_to_hhmm(t) for t in blocked_times}

        start_utc, end_utc = _msk_day_bounds_utc(day)
        booked_start_ats = await orders_repo.list_order_start_at_between(
            session=session,
            start_at=start_utc,
            end_at=end_utc,
        )
        booked = {dt.astimezone(MOSCOW_TZ).strftime("%H:%M") for dt in booked_start_ats}

        return _compute_available_slots(
            policy=self.policy,
            is_day_off=False,
            blocked=blocked,
            booked=booked,
        )

    async def get_disabled_dates(
        self,
        *,
        session: AsyncSession,
        today: date,
    ) -> set[date]:
        start_date = today
        end_date = today + timedelta(days=self.policy.days_ahead)

        day_off_dates = await exc_repo.list_day_off_dates(
            session=session,
            start_date=start_date,
            end_date_inclusive=end_date,
        )

        blocked_by_date = await exc_repo.list_blocked_slots_between(
            session=session,
            start_date=start_date,
            end_date_inclusive=end_date,
        )

        start_utc, _ = _msk_day_bounds_utc(start_date)
        end_utc = compose_start_at_utc(
            chosen_date=end_date + timedelta(days=1), chosen_time=time(0, 0)
        )
        booked_start_ats = await orders_repo.list_order_start_at_between(
            session=session,
            start_at=start_utc,
            end_at=end_utc,
        )
        booked_by_date: dict[date, set[str]] = {}
        for dt in booked_start_ats:
            dt_msk = dt.astimezone(MOSCOW_TZ)
            booked_by_date.setdefault(dt_msk.date(), set()).add(
                dt_msk.strftime("%H:%M")
            )

        disabled: set[date] = set()
        cur = start_date
        while cur <= end_date:
            if cur in day_off_dates:
                disabled.add(cur)
            else:
                blocked = {_time_to_hhmm(t) for t in blocked_by_date.get(cur, set())}
                booked = booked_by_date.get(cur, set())
                if not _compute_available_slots(
                    policy=self.policy,
                    is_day_off=False,
                    blocked=blocked,
                    booked=booked,
                ):
                    disabled.add(cur)
            cur += timedelta(days=1)

        return disabled

    async def is_slot_available(
        self,
        *,
        session: AsyncSession,
        day: date,
        slot_hhmm: str,
    ) -> bool:
        # Validate slot belongs to the schedule policy.
        if slot_hhmm not in set(list_time_slots(self.policy)):
            return False
        slots = await self.get_available_slots(session=session, day=day)
        return slot_hhmm in set(slots)


__all__ = [
    "CalendarAvailabilityService",
    "_compute_available_slots",
    "_parse_time_hhmm",
]

from __future__ import annotations

from datetime import date, time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models.blocked_slot import BlockedSlot
from infra.db.models.day_off import DayOff


async def list_day_off_dates(
    *,
    session: AsyncSession,
    start_date: date,
    end_date_inclusive: date,
) -> set[date]:
    result = await session.execute(
        select(DayOff.date).where(DayOff.date.between(start_date, end_date_inclusive))
    )
    return set(result.scalars().all())


async def is_day_off(*, session: AsyncSession, day: date) -> bool:
    result = await session.execute(select(DayOff.date).where(DayOff.date == day))
    return result.scalar_one_or_none() is not None


async def toggle_day_off(
    *,
    session: AsyncSession,
    day: date,
    reason: str | None = None,
) -> bool:
    """
    Toggle day off for a date.

    Returns:
        True if the date is now marked as day off (created),
        False if it was unmarked (deleted).
    """
    existing = await session.execute(select(DayOff).where(DayOff.date == day))
    row = existing.scalar_one_or_none()
    if row is not None:
        await session.delete(row)
        await session.flush()
        return False

    session.add(DayOff(date=day, reason=reason))
    await session.flush()
    return True


async def list_blocked_slots_for_date(
    *,
    session: AsyncSession,
    day: date,
) -> set[time]:
    result = await session.execute(
        select(BlockedSlot.time).where(BlockedSlot.date == day)
    )
    return set(result.scalars().all())


async def list_blocked_slots_between(
    *,
    session: AsyncSession,
    start_date: date,
    end_date_inclusive: date,
) -> dict[date, set[time]]:
    result = await session.execute(
        select(BlockedSlot.date, BlockedSlot.time).where(
            BlockedSlot.date.between(start_date, end_date_inclusive)
        )
    )
    out: dict[date, set[time]] = {}
    for d, t in result.all():
        out.setdefault(d, set()).add(t)
    return out


async def toggle_blocked_slot(
    *,
    session: AsyncSession,
    day: date,
    slot_time: time,
    reason: str | None = None,
) -> bool:
    """
    Toggle a blocked slot.

    Returns:
        True if the slot is now blocked (created),
        False if it was unblocked (deleted).
    """
    existing = await session.execute(
        select(BlockedSlot).where(
            BlockedSlot.date == day,
            BlockedSlot.time == slot_time,
        )
    )
    row = existing.scalar_one_or_none()
    if row is not None:
        await session.delete(row)
        await session.flush()
        return False

    session.add(BlockedSlot(date=day, time=slot_time, reason=reason))
    await session.flush()
    return True


async def delete_blocked_slots_for_date(*, session: AsyncSession, day: date) -> int:
    """
    Utility for bulk cleanup (not used by UI yet).
    Returns deleted rows count if supported by backend.
    """
    res = await session.execute(delete(BlockedSlot).where(BlockedSlot.date == day))
    try:
        return int(res.rowcount or 0)
    except Exception:
        return 0

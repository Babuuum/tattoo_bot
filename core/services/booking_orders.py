from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories.orders import create_order
from core.repositories.users import get_or_create_user
from core.services.schedule import compose_start_at_utc


@dataclass(frozen=True, slots=True)
class BookingDraft:
    calendar_date: str
    calendar_time: str


def _parse_time_hhmm(value: str) -> time:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("invalid time format")
    h, m = int(parts[0]), int(parts[1])
    return time(hour=h, minute=m)


def _parse_date_iso(value: str) -> date:
    return date.fromisoformat(value)


async def persist_booking_as_order(
    *,
    session: AsyncSession,
    tg_id: int,
    tg_nickname: str,
    calendar_date: str,
    calendar_time: str,
) -> int:
    chosen_date = _parse_date_iso(calendar_date)
    chosen_time = _parse_time_hhmm(calendar_time)
    start_at_utc = compose_start_at_utc(
        chosen_date=chosen_date, chosen_time=chosen_time
    )

    async with session.begin():
        user = await get_or_create_user(
            session=session,
            tg_id=tg_id,
            tg_nickname=tg_nickname,
        )
        order = await create_order(
            session=session, user_id=user.id, start_at=start_at_utc
        )

    return order.id

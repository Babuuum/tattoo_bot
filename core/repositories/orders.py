from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models.order import Order


async def create_order(
    *,
    session: AsyncSession,
    user_id: int,
    start_at: datetime,
    tattoo_id: int | None = None,
    sessions: int | None = None,
    price: int | None = None,
) -> Order:
    order = Order(
        user_id=user_id,
        tattoo_id=tattoo_id,
        sessions=sessions,
        price=price,
        start_at=start_at,
    )
    session.add(order)
    await session.flush()
    return order


async def list_order_start_at_between(
    *,
    session: AsyncSession,
    start_at: datetime,
    end_at: datetime,
) -> list[datetime]:
    """
    Return order.start_at values in [start_at, end_at).

    Used for availability computations.
    """
    result = await session.execute(
        select(Order.start_at)
        .where(Order.start_at >= start_at)
        .where(Order.start_at < end_at)
    )
    return list(result.scalars().all())


async def exists_order_with_start_at(
    *, session: AsyncSession, start_at: datetime
) -> bool:
    result = await session.execute(select(Order.id).where(Order.start_at == start_at))
    return result.scalar_one_or_none() is not None

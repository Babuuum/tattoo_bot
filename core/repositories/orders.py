from __future__ import annotations

from datetime import datetime

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

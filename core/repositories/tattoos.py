from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models.tattoo import Tattoo


async def list_tattoos_by_style(
    *,
    session: AsyncSession,
    style_id: int,
    limit: int,
    offset: int,
) -> list[Tattoo]:
    result = await session.execute(
        select(Tattoo)
        .where(Tattoo.style_id == style_id)
        .order_by(desc(Tattoo.views), Tattoo.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_tattoo(*, session: AsyncSession, tattoo_id: int) -> Tattoo | None:
    result = await session.execute(select(Tattoo).where(Tattoo.id == tattoo_id))
    return result.scalar_one_or_none()


async def create_tattoo(
    *,
    session: AsyncSession,
    name: str,
    style_id: int,
    price: int | None,
    photo_file_id: str | None,
) -> Tattoo:
    tattoo = Tattoo(
        name=name, style_id=style_id, price=price, photo_file_id=photo_file_id
    )
    session.add(tattoo)
    try:
        await session.flush()
    except IntegrityError as e:
        raise ValueError("tattoo already exists") from e
    return tattoo

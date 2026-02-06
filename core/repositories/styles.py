from __future__ import annotations

from sqlalchemy import Select, desc, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models.style import Style
from infra.db.models.tattoo import Tattoo


async def get_style(*, session: AsyncSession, style_id: int) -> Style | None:
    result = await session.execute(select(Style).where(Style.id == style_id))
    return result.scalar_one_or_none()


async def increment_style_views(*, session: AsyncSession, style_id: int) -> None:
    await session.execute(
        update(Style).where(Style.id == style_id).values(views=Style.views + 1)
    )


async def list_styles_with_top_tattoo(
    *, session: AsyncSession
) -> list[tuple[Style, Tattoo | None]]:
    ranked = select(
        Tattoo.id.label("tattoo_id"),
        Tattoo.style_id.label("style_id"),
        func.row_number()
        .over(partition_by=Tattoo.style_id, order_by=(desc(Tattoo.views), Tattoo.id))
        .label("rn"),
    ).subquery()

    stmt: Select = (
        select(Style, Tattoo)
        .outerjoin(ranked, ranked.c.style_id == Style.id)
        .outerjoin(Tattoo, Tattoo.id == ranked.c.tattoo_id)
        .where((ranked.c.rn == 1) | (ranked.c.rn.is_(None)))
        .order_by(Style.name.asc())
    )

    result = await session.execute(stmt)
    return [(style, tattoo) for style, tattoo in result.all()]


async def list_styles(*, session: AsyncSession) -> list[Style]:
    result = await session.execute(select(Style).order_by(Style.name.asc()))
    return list(result.scalars().all())


async def create_style(*, session: AsyncSession, name: str) -> Style:
    style = Style(name=name)
    session.add(style)
    try:
        await session.flush()
    except IntegrityError as e:
        raise ValueError("style already exists") from e
    return style

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models.user import User


async def get_user_by_tg_id(*, session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_or_create_user(
    *,
    session: AsyncSession,
    tg_id: int,
    tg_nickname: str,
) -> User:
    user = await get_user_by_tg_id(session=session, tg_id=tg_id)
    if user is not None:
        if user.tg_nickname != tg_nickname:
            user.tg_nickname = tg_nickname
        return user

    user = User(tg_id=tg_id, tg_nickname=tg_nickname)
    session.add(user)
    await session.flush()
    return user

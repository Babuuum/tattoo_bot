from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine


def create_async_engine(database_url: str):
    return _create_async_engine(database_url, pool_pre_ping=True)


def create_sessionmaker(
    database_url: str | None = None,
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    if engine is None:
        if database_url is None:
            raise ValueError("database_url is required when engine is not provided")
        engine = create_async_engine(database_url)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session

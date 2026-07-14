from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.game_service.config import get_settings


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(settings.postgres_dsn.get_secret_value(), pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def database_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session

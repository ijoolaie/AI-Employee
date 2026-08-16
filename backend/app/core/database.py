"""Async SQLAlchemy engine/session management.

Uses NullPool because the application is also exercised from Windows
asyncio/Proactor event loops where pooled asyncpg connections can otherwise
be reused by a different event loop and cause:

    AttributeError: 'NoneType' object has no attribute 'send'

NullPool guarantees that connections are not retained across sessions/event
loops. This is especially important for pytest and Celery on Windows.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


settings = get_settings()


# IMPORTANT:
# Do not use SQLAlchemy's default QueuePool here.
# On Windows/Proactor, asyncpg connections retained by QueuePool can belong
# to a previous event loop and later fail with:
#     AttributeError: 'NoneType' object has no attribute 'send'
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an API database session with transaction handling."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def worker_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a Celery-worker DB session isolated from other event loops.

    Celery tasks on Windows may create a fresh event loop with asyncio.run().
    NullPool prevents asyncpg connections from surviving across those loops.
    """
    worker_engine: AsyncEngine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        poolclass=NullPool,
    )

    worker_session_factory = async_sessionmaker(
        worker_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    try:
        async with worker_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    finally:
        await worker_engine.dispose()

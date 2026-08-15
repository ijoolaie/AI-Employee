"""Async SQLAlchemy engine/session management.

The API uses a normal pooled async engine. Celery Run workers on Windows use a
separate per-event-loop engine with ``NullPool`` so asyncpg connections are never
reused across the event loops created by ``asyncio.run()``.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
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

    ``asyncio.run()`` creates and closes an event loop for each Celery task.
    SQLAlchemy's normal QueuePool may retain asyncpg connections that belong to
    a previous loop. On Windows/Proactor this can surface as
    ``_proactor.send`` / ``NoneType.send`` errors. A worker-local ``NullPool``
    ensures every task gets a fresh connection and no connection is retained
    after the session/engine is disposed.
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

"""PostgreSQL integration coverage for report artifact advisory-lock serialization.

CI supplies a migrated PostgreSQL database through DATABASE_URL. The test uses
independent sessions and the same lock-key derivation as report.service, so it
checks the database behavior rather than mocking AsyncSession.execute.
"""

import asyncio
import hashlib
import os
import uuid

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


@pytest.mark.asyncio
async def test_report_advisory_lock_serializes_concurrent_sessions():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")

    tenant_id = uuid.uuid4()
    source_id = uuid.uuid4()
    lock_key = int.from_bytes(
        hashlib.sha256(f"report:{tenant_id}:{source_id}".encode("utf-8")).digest()[:8],
        "big",
        signed=True,
    )

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    second_started = asyncio.Event()
    second_acquired = asyncio.Event()

    async def acquire_lock_in_second_transaction():
        async with sessions() as second:
            async with second.begin():
                second_started.set()
                await second.execute(select(func.pg_advisory_xact_lock(lock_key)))
                second_acquired.set()

    second_task = None
    try:
        async with sessions() as first:
            transaction = await first.begin()
            await first.execute(select(func.pg_advisory_xact_lock(lock_key)))

            second_task = asyncio.create_task(acquire_lock_in_second_transaction())
            await asyncio.wait_for(second_started.wait(), timeout=5)

            # Wait until PostgreSQL confirms that the second backend is blocked
            # on an advisory lock; this avoids relying on arbitrary sleep timing.
            deadline = asyncio.get_running_loop().time() + 5
            waiting = False
            while asyncio.get_running_loop().time() < deadline:
                waiting = bool(
                    await first.scalar(
                        text(
                            "SELECT EXISTS ("
                            " SELECT 1 FROM pg_stat_activity"
                            " WHERE wait_event_type = 'Lock'"
                            " AND wait_event = 'advisory'"
                            " AND query ILIKE '%pg_advisory_xact_lock%'"
                            ")"
                        )
                    )
                )
                if waiting:
                    break
                await asyncio.sleep(0.05)

            assert waiting, "second PostgreSQL session never waited on the report advisory lock"
            assert not second_acquired.is_set()

            await transaction.commit()
            await asyncio.wait_for(second_task, timeout=5)
            assert second_acquired.is_set()
    finally:
        if second_task is not None and not second_task.done():
            second_task.cancel()
            await asyncio.gather(second_task, return_exceptions=True)
        await engine.dispose()

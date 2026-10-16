"""PostgreSQL integration coverage for report artifact advisory-lock serialization.

CI supplies PostgreSQL through DATABASE_URL. Independent sessions exercise the
same transaction-scoped advisory lock used by report.service, without mocking
AsyncSession.execute or depending on pg_stat_activity polling.
"""

import asyncio
import hashlib
import os
import uuid

import pytest
from sqlalchemy import func, select
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
    second_probe_completed = asyncio.Event()
    second_acquired = asyncio.Event()
    second_probe_result = None

    async def acquire_lock_in_second_transaction():
        nonlocal second_probe_result
        async with sessions() as second:
            async with second.begin():
                second_started.set()
                # This non-blocking PostgreSQL primitive proves the first
                # transaction owns the lock when it returns False.
                second_probe_result = bool(
                    await second.scalar(select(func.pg_try_advisory_xact_lock(lock_key)))
                )
                second_probe_completed.set()
                await second.execute(select(func.pg_advisory_xact_lock(lock_key)))
                second_acquired.set()

    second_task = None
    try:
        async with sessions() as first:
            transaction = await first.begin()
            await first.execute(select(func.pg_advisory_xact_lock(lock_key)))

            second_task = asyncio.create_task(acquire_lock_in_second_transaction())
            await asyncio.wait_for(second_started.wait(), timeout=5)
            await asyncio.wait_for(second_probe_completed.wait(), timeout=5)

            assert second_probe_result is False, (
                "second PostgreSQL session unexpectedly acquired the lock "
                "while the first transaction still held it"
            )
            assert not second_acquired.is_set()

            await transaction.commit()
            await asyncio.wait_for(second_task, timeout=5)
            assert second_acquired.is_set()
    finally:
        if second_task is not None and not second_task.done():
            second_task.cancel()
            await asyncio.gather(second_task, return_exceptions=True)
        await engine.dispose()

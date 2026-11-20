from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.v1 import operations
from app.models.outbox import OutboxMessage
from app.models.tenant import Tenant
from app.services import outbox_service


def _dedicated_test_database_url() -> str | None:
    url = (
        os.environ.get("LIFECYCLE_TEST_DATABASE_URL")
        or os.environ.get("SUPPORT_TEST_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.username not in {"support_test_user", "aiep"}
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433, 15435}
        or parsed.database not in {"support_test", "ai_employee_lifecycle_test"}
        or not parsed.password
    ):
        raise RuntimeError("URL must target the dedicated local support_test database; refusing to run.")
    return url


@pytest.mark.asyncio
async def test_concurrent_dead_letter_replay_is_serialized_by_tenant_row_lock(monkeypatch):
    db_url = _dedicated_test_database_url()
    if db_url is None:
        pytest.skip("Dedicated PostgreSQL support_test database is not configured")

    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    tenant_id = uuid.uuid4()
    message_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        name="Outbox replay concurrency test",
        slug=f"outbox-replay-{tenant_id.hex}",
        status="active",
        tenant_kind="vendor",
        settings={},
    )
    message = OutboxMessage(
        id=message_id,
        tenant_id=tenant_id,
        kind="workflow.execute",
        payload={"test_marker": "concurrent-replay"},
        status="dead",
        attempts=5,
        dead_at=datetime.now(timezone.utc),
    )
    try:
        async with sessions() as db:
            db.add_all([tenant, message])
            await db.commit()

        first_replay_entered = asyncio.Event()
        second_replay_query_started = asyncio.Event()
        release_first_replay = asyncio.Event()
        original_replay = outbox_service.replay
        replay_calls = 0

        async def pause_first_replay(db, row):
            nonlocal replay_calls
            replay_calls += 1
            if replay_calls == 1:
                first_replay_entered.set()
                await release_first_replay.wait()
            return await original_replay(db, row)

        monkeypatch.setattr(outbox_service, "replay", pause_first_replay)
        context = SimpleNamespace(tenant_id=tenant_id)

        class SecondReplaySession(AsyncSession):
            async def execute(self, statement, *args, **kwargs):
                second_replay_query_started.set()
                return await super().execute(statement, *args, **kwargs)

        second_sessions = async_sessionmaker(
            engine, class_=SecondReplaySession, expire_on_commit=False, autoflush=False
        )

        async def invoke_replay(session_factory=sessions):
            async with session_factory() as db:
                return await operations.replay_dead_letter(message_id, context, db)

        first = asyncio.create_task(invoke_replay())
        await asyncio.wait_for(first_replay_entered.wait(), timeout=5)
        second = asyncio.create_task(invoke_replay(second_sessions))
        await asyncio.wait_for(second_replay_query_started.wait(), timeout=5)
        release_first_replay.set()

        first_result = await asyncio.wait_for(first, timeout=5)
        assert first_result.data["status"] == "pending"
        with pytest.raises(HTTPException) as rejected:
            await asyncio.wait_for(second, timeout=5)
        assert rejected.value.status_code == 409

        async with sessions() as db:
            persisted = await db.get(OutboxMessage, message_id)
            assert persisted is not None
            assert persisted.status == "pending"
            assert persisted.attempts == 0
            assert persisted.dead_at is None
            assert replay_calls == 1
    finally:
        async with sessions() as db:
            await db.execute(delete(OutboxMessage).where(OutboxMessage.id == message_id))
            await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
            await db.commit()
        await engine.dispose()\n
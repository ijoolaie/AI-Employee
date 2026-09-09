"""Focused regression coverage for concurrent outbox deduplication."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.outbox import OutboxMessage
from app.services import outbox_service


@pytest.mark.asyncio
async def test_enqueue_recovers_from_concurrent_dedupe_violation():
    tenant_id = uuid.uuid4()
    winner = OutboxMessage(tenant_id=tenant_id, kind="test", payload={"ok": True}, dedupe_key="race-1")
    lookup_count = 0
    flush_count = 0

    class Result:
        def scalar_one_or_none(self):
            return None if lookup_count == 1 else winner

    class Nested:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DB:
        def add(self, item):
            assert isinstance(item, OutboxMessage)

        async def execute(self, statement):
            nonlocal lookup_count
            lookup_count += 1
            return Result()

        async def flush(self):
            nonlocal flush_count
            flush_count += 1
            raise IntegrityError("insert", {}, Exception("duplicate"))

        def begin_nested(self):
            return Nested()

    result = await outbox_service.enqueue(
        DB(),
        kind="test",
        payload={"ok": True},
        tenant_id=tenant_id,
        dedupe_key="race-1",
    )

    assert result is winner
    assert lookup_count == 2
    assert flush_count == 1

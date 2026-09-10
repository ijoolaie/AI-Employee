"""Focused regression coverage for BillingEvent admission concurrency."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.billing import BillingEvent
from app.services import billing_service


@pytest.mark.asyncio
async def test_record_event_recovers_from_concurrent_unique_violation():
    provider = "stripe"
    provider_event_id = f"evt_{uuid.uuid4().hex}"
    winner = BillingEvent(
        provider=provider,
        provider_event_id=provider_event_id,
        event_type="invoice.paid",
        payload={"winner": True},
        status="processed",
    )
    lookup_count = 0
    added = []

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
            assert isinstance(item, BillingEvent)
            added.append(item)

        async def execute(self, statement):
            nonlocal lookup_count
            lookup_count += 1
            return Result()

        async def flush(self):
            raise IntegrityError("insert", {}, Exception("duplicate"))

        def begin_nested(self):
            return Nested()

    result = await billing_service.record_event(
        DB(),
        tenant_id=None,
        provider=provider,
        provider_event_id=provider_event_id,
        event_type="invoice.paid",
        payload={"winner": False},
    )

    assert result is winner
    assert lookup_count == 2
    assert len(added) == 1
    assert added[0] is not winner

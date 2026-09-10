"""Regression coverage for Stripe lifecycle webhook ordering protection."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import stripe_service


@pytest.mark.asyncio
async def test_lifecycle_event_lock_rejects_stale_provider_event():
    tenant_id = uuid.uuid4()
    subscription_id = uuid.uuid4()
    subscription = SimpleNamespace(id=subscription_id, tenant_id=tenant_id)

    latest_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [
                {"stripe_event_created_at": 200},
                {"stripe_event_created_at": 150},
            ]
        )
    )
    lock_result = SimpleNamespace(scalar_one=lambda: subscription)
    db = SimpleNamespace(execute=AsyncMock(side_effect=[lock_result, latest_result]))

    locked, stale = await stripe_service._lock_subscription_for_lifecycle(
        db,
        subscription_id=subscription_id,
        event_created_at=150,
    )

    assert locked is subscription
    assert stale is True
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_lifecycle_event_lock_accepts_newer_provider_event():
    tenant_id = uuid.uuid4()
    subscription_id = uuid.uuid4()
    subscription = SimpleNamespace(id=subscription_id, tenant_id=tenant_id)

    latest_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [{"stripe_event_created_at": 100}]
        )
    )
    lock_result = SimpleNamespace(scalar_one=lambda: subscription)
    db = SimpleNamespace(execute=AsyncMock(side_effect=[lock_result, latest_result]))

    locked, stale = await stripe_service._lock_subscription_for_lifecycle(
        db,
        subscription_id=subscription_id,
        event_created_at=150,
    )

    assert locked is subscription
    assert stale is False
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_lifecycle_event_lock_ignores_legacy_rows_without_provider_timestamp():
    tenant_id = uuid.uuid4()
    subscription_id = uuid.uuid4()
    subscription = SimpleNamespace(id=subscription_id, tenant_id=tenant_id)

    latest_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [
                {"id": "legacy"},
                {"stripe_event_created_at": None},
                {"stripe_event_created_at": "not-a-timestamp"},
            ]
        )
    )
    lock_result = SimpleNamespace(scalar_one=lambda: subscription)
    db = SimpleNamespace(execute=AsyncMock(side_effect=[lock_result, latest_result]))

    _, stale = await stripe_service._lock_subscription_for_lifecycle(
        db,
        subscription_id=subscription_id,
        event_created_at=1,
    )

    assert stale is False

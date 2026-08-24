from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.billing_service import (
    _period_end,
    _period_start,
    process_subscription_lifecycle,
)


def _subscription(
    *,
    status="active",
    current_period_start=None,
    current_period_end=None,
    cancel_at_period_end=False,
    canceled_at=None,
    trial_ends_at=None,
):
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    start = current_period_start or _period_start(now)
    end = current_period_end or _period_end(start)

    return SimpleNamespace(
        status=status,
        current_period_start=start,
        current_period_end=end,
        cancel_at_period_end=cancel_at_period_end,
        canceled_at=canceled_at,
        trial_ends_at=trial_ends_at,
    )


@pytest.mark.asyncio
async def test_expired_trial_moves_to_past_due():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    sub = _subscription(
        status="trialing",
        trial_ends_at=now - timedelta(seconds=1),
    )

    result = await process_subscription_lifecycle(db, subscription=sub, now=now)

    assert result.status == "past_due"
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_at_period_end_becomes_canceled_after_period_end():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    old_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)

    sub = _subscription(
        status="active",
        current_period_start=old_start,
        current_period_end=old_end,
        cancel_at_period_end=True,
    )

    result = await process_subscription_lifecycle(db, subscription=sub, now=now)

    assert result.status == "canceled"
    assert result.cancel_at_period_end is False
    assert result.canceled_at == now
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_active_subscription_renews_into_current_calendar_period():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    old_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)

    sub = _subscription(
        status="active",
        current_period_start=old_start,
        current_period_end=old_end,
    )

    result = await process_subscription_lifecycle(db, subscription=sub, now=now)

    assert result.status == "active"
    assert result.current_period_start == _period_start(now)
    assert result.current_period_end == _period_end(_period_start(now))
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_active_subscription_does_not_renew_before_period_end():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    start = _period_start(now)
    end = _period_end(start)

    sub = _subscription(
        status="active",
        current_period_start=start,
        current_period_end=end,
    )

    result = await process_subscription_lifecycle(db, subscription=sub, now=now)

    assert result.current_period_start == start
    assert result.current_period_end == end
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_canceled_subscription_does_not_auto_renew():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    old_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)

    sub = _subscription(
        status="canceled",
        current_period_start=old_start,
        current_period_end=old_end,
        canceled_at=old_end,
    )

    result = await process_subscription_lifecycle(db, subscription=sub, now=now)

    assert result.status == "canceled"
    assert result.current_period_start == old_start
    assert result.current_period_end == old_end
    db.flush.assert_not_awaited()

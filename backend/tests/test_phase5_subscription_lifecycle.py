from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictError
from app.services import billing_service
from app.services.billing_service import _period_end, _period_start, process_subscription_lifecycle


def _subscription(*, status="active", provider="manual", current_period_start=None, current_period_end=None, cancel_at_period_end=False, canceled_at=None, trial_ends_at=None):
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    start = current_period_start or _period_start(now)
    end = current_period_end or _period_end(start)
    return SimpleNamespace(status=status, provider=provider, current_period_start=start, current_period_end=end, cancel_at_period_end=cancel_at_period_end, canceled_at=canceled_at, trial_ends_at=trial_ends_at)


@pytest.mark.asyncio
async def test_expired_trial_moves_to_past_due():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    result = await process_subscription_lifecycle(db, subscription=_subscription(status="trialing", trial_ends_at=now - timedelta(seconds=1)), now=now)
    assert result.status == "past_due"
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_at_period_end_becomes_canceled_after_period_end():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    old_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
    result = await process_subscription_lifecycle(db, subscription=_subscription(status="active", current_period_start=old_start, current_period_end=old_end, cancel_at_period_end=True), now=now)
    assert result.status == "canceled"
    assert result.cancel_at_period_end is False
    assert result.canceled_at == now
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_active_subscription_renews_into_current_calendar_period():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    old_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
    result = await process_subscription_lifecycle(db, subscription=_subscription(provider="manual", status="active", current_period_start=old_start, current_period_end=old_end), now=now)
    assert result.status == "active"
    assert result.current_period_start == _period_start(now)
    assert result.current_period_end == _period_end(_period_start(now))
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_external_subscription_does_not_auto_renew_after_period_end():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    old_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
    result = await process_subscription_lifecycle(db, subscription=_subscription(provider="stripe", status="active", current_period_start=old_start, current_period_end=old_end), now=now)
    assert result.status == "active"
    assert result.current_period_start == old_start
    assert result.current_period_end == old_end
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_active_manual_subscription_does_not_renew_before_period_end():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    start = _period_start(now)
    end = _period_end(start)
    result = await process_subscription_lifecycle(db, subscription=_subscription(provider="manual", status="active", current_period_start=start, current_period_end=end), now=now)
    assert result.current_period_start == start
    assert result.current_period_end == end
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_canceled_subscription_does_not_auto_renew():
    db = AsyncMock()
    now = datetime(2026, 8, 23, tzinfo=timezone.utc)
    old_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
    result = await process_subscription_lifecycle(db, subscription=_subscription(status="canceled", current_period_start=old_start, current_period_end=old_end, canceled_at=old_end), now=now)
    assert result.status == "canceled"
    assert result.current_period_start == old_start
    assert result.current_period_end == old_end
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_external_subscription_cannot_be_changed_by_local_plan_mutation(monkeypatch):
    db = AsyncMock()
    sub = SimpleNamespace(id="sub-1", plan_id="plan-old", status="active", provider="stripe", cancel_at_period_end=False, canceled_at=None)
    plan = SimpleNamespace(id="plan-new", code="business", is_active=True)
    monkeypatch.setattr(billing_service, "ensure_subscription", AsyncMock(return_value=sub))
    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: plan)
    with pytest.raises(ConflictError, match="External-provider subscriptions"):
        await billing_service.change_plan(db, tenant_id="00000000-0000-0000-0000-000000000001", plan_code="business", actor_id=None)
    assert sub.plan_id == "plan-old"
    assert sub.status == "active"
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("at_period_end", [True, False])
async def test_external_subscription_cannot_be_canceled_locally(monkeypatch, at_period_end):
    db = AsyncMock()
    sub = SimpleNamespace(
        id="sub-1",
        plan_id="plan-old",
        status="active",
        provider="stripe",
        cancel_at_period_end=False,
        canceled_at=None,
    )
    monkeypatch.setattr(billing_service, "ensure_subscription", AsyncMock(return_value=sub))
    with pytest.raises(ConflictError, match="External-provider subscriptions"):
        await billing_service.cancel_subscription(
            db,
            tenant_id="00000000-0000-0000-0000-000000000001",
            at_period_end=at_period_end,
            actor_id=None,
        )
    assert sub.status == "active"
    assert sub.cancel_at_period_end is False
    assert sub.canceled_at is None
    db.flush.assert_not_awaited()

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictError
from app.services import billing_service


@pytest.mark.asyncio
@pytest.mark.parametrize("quota_name", ["enforce_employee_quota", "enforce_workflow_quota"])
@pytest.mark.parametrize("status", ["past_due", "canceled"])
async def test_resource_quota_rejects_inactive_subscription(
    monkeypatch, quota_name, status
):
    db = AsyncMock()
    subscription = SimpleNamespace(
        status=status,
        plan=SimpleNamespace(
            code="business",
            max_employees=20,
            max_workflows=25,
        ),
    )

    monkeypatch.setattr(
        billing_service,
        "_lock_tenant_for_quota",
        AsyncMock(),
    )
    monkeypatch.setattr(
        billing_service,
        "get_subscription",
        AsyncMock(return_value=subscription),
    )
    usage = AsyncMock(return_value={"employees": 0, "workflows": 0})
    monkeypatch.setattr(billing_service, "monthly_usage", usage)

    quota_check = getattr(billing_service, quota_name)
    with pytest.raises(ConflictError, match="Subscription is not active"):
        await quota_check(
            db,
            tenant_id="00000000-0000-0000-0000-000000000001",
        )

    usage.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("quota_name", ["enforce_employee_quota", "enforce_workflow_quota"])
@pytest.mark.parametrize("status", ["active", "trialing"])
async def test_resource_quota_allows_active_subscription_states(
    monkeypatch, quota_name, status
):
    db = AsyncMock()
    subscription = SimpleNamespace(
        status=status,
        plan=SimpleNamespace(
            code="business",
            max_employees=20,
            max_workflows=25,
        ),
    )

    monkeypatch.setattr(
        billing_service,
        "_lock_tenant_for_quota",
        AsyncMock(),
    )
    monkeypatch.setattr(
        billing_service,
        "get_subscription",
        AsyncMock(return_value=subscription),
    )
    usage = AsyncMock(return_value={"employees": 0, "workflows": 0})
    monkeypatch.setattr(billing_service, "monthly_usage", usage)

    quota_check = getattr(billing_service, quota_name)
    await quota_check(
        db,
        tenant_id="00000000-0000-0000-0000-000000000001",
    )

    usage.assert_awaited_once()

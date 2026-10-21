from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import billing_service, license_service


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _VendorDB:
    async def execute(self, _statement):
        return _Result(SimpleNamespace(tenant_kind="vendor"))


@pytest.mark.asyncio
async def test_vendor_run_execution_does_not_require_commercial_license_or_subscription(monkeypatch):
    license_check = AsyncMock()
    subscription_check = AsyncMock()
    monkeypatch.setattr(license_service, "assert_execution_license", license_check)
    monkeypatch.setattr(billing_service, "get_subscription", subscription_check)

    await billing_service.assert_run_execution_entitlement(
        _VendorDB(), tenant_id="vendor-tenant"
    )

    license_check.assert_not_awaited()
    subscription_check.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_run_quota_does_not_require_commercial_license_or_subscription(monkeypatch):
    license_check = AsyncMock()
    subscription_check = AsyncMock()
    monkeypatch.setattr(license_service, "assert_execution_license", license_check)
    monkeypatch.setattr(billing_service, "get_subscription", subscription_check)
    monkeypatch.setattr(
        billing_service,
        "_lock_tenant_for_quota",
        AsyncMock(return_value=SimpleNamespace(tenant_kind="vendor")),
    )

    await billing_service.enforce_run_quota(object(), tenant_id="vendor-tenant")

    license_check.assert_not_awaited()
    subscription_check.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_tool_feature_entitlement_does_not_require_commercial_license(monkeypatch):
    license_check = AsyncMock()
    monkeypatch.setattr(license_service, "assert_execution_license", license_check)

    result = await license_service.assert_feature_entitlement(
        _VendorDB(), tenant_id="vendor-tenant", feature_code="tool:send_email"
    )

    assert result is None
    license_check.assert_not_awaited()

@pytest.mark.asyncio
async def test_vendor_employee_quota_does_not_require_subscription_or_plan_quota(monkeypatch):
    subscription_check = AsyncMock()
    usage_check = AsyncMock()
    monkeypatch.setattr(billing_service, "get_subscription", subscription_check)
    monkeypatch.setattr(billing_service, "monthly_usage", usage_check)
    monkeypatch.setattr(
        billing_service,
        "_lock_tenant_for_quota",
        AsyncMock(return_value=SimpleNamespace(tenant_kind="vendor")),
    )

    await billing_service.enforce_employee_quota(object(), tenant_id="vendor-tenant")

    subscription_check.assert_not_awaited()
    usage_check.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_workflow_quota_does_not_require_subscription_or_plan_quota(monkeypatch):
    subscription_check = AsyncMock()
    usage_check = AsyncMock()
    monkeypatch.setattr(billing_service, "get_subscription", subscription_check)
    monkeypatch.setattr(billing_service, "monthly_usage", usage_check)
    monkeypatch.setattr(
        billing_service,
        "_lock_tenant_for_quota",
        AsyncMock(return_value=SimpleNamespace(tenant_kind="vendor")),
    )

    await billing_service.enforce_workflow_quota(object(), tenant_id="vendor-tenant")

    subscription_check.assert_not_awaited()
    usage_check.assert_not_awaited()

@pytest.mark.parametrize("tenant_kind", ["reseller", "customer"])
@pytest.mark.asyncio
async def test_reseller_and_customer_employee_and_workflow_quotas_still_use_subscription(
    tenant_kind, monkeypatch
):
    subscription = SimpleNamespace(
        status="active",
        plan=SimpleNamespace(max_employees=3, max_workflows=3),
    )
    subscription_check = AsyncMock(return_value=subscription)
    usage_check = AsyncMock(return_value={"employees": 0, "workflows": 0})
    monkeypatch.setattr(billing_service, "get_subscription", subscription_check)
    monkeypatch.setattr(billing_service, "monthly_usage", usage_check)
    monkeypatch.setattr(
        billing_service,
        "_lock_tenant_for_quota",
        AsyncMock(return_value=SimpleNamespace(tenant_kind=tenant_kind)),
    )

    await billing_service.enforce_employee_quota(object(), tenant_id=f"{tenant_kind}-tenant")
    await billing_service.enforce_workflow_quota(object(), tenant_id=f"{tenant_kind}-tenant")

    assert subscription_check.await_count == 2
    assert usage_check.await_count == 2


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

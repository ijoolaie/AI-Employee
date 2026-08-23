from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai.tool_registry import registry
from app.core.exceptions import ConflictError
from app.services import license_service


def _license(*, feature_codes):
    return SimpleNamespace(
        id="license-1",
        feature_codes=feature_codes,
    )


class _DB:
    def __init__(self, entitlement=None):
        self.entitlement = entitlement

    async def execute(self, _statement):
        return SimpleNamespace(
            scalar_one_or_none=lambda: self.entitlement,
        )


@pytest.mark.asyncio
async def test_feature_entitlement_allows_feature_listed_on_license(monkeypatch):
    db = _DB()
    license_row = _license(feature_codes=["tool:send_email"])

    monkeypatch.setattr(
        license_service,
        "assert_execution_license",
        AsyncMock(return_value=license_row),
    )

    await license_service.assert_feature_entitlement(
        db,
        tenant_id="tenant-1",
        feature_code="tool:send_email",
    )


@pytest.mark.asyncio
async def test_feature_entitlement_rejects_feature_missing_from_restricted_license(monkeypatch):
    db = _DB()
    license_row = _license(feature_codes=["tool:sales_forecast"])

    monkeypatch.setattr(
        license_service,
        "assert_execution_license",
        AsyncMock(return_value=license_row),
    )

    with pytest.raises(
        ConflictError,
        match="Commercial license does not include feature",
    ):
        await license_service.assert_feature_entitlement(
            db,
            tenant_id="tenant-1",
            feature_code="tool:send_email",
        )


@pytest.mark.asyncio
async def test_feature_entitlement_rejects_disabled_tenant_entitlement(monkeypatch):
    db = _DB(
        entitlement=SimpleNamespace(
            is_enabled=False,
        )
    )
    license_row = _license(feature_codes=[])

    monkeypatch.setattr(
        license_service,
        "assert_execution_license",
        AsyncMock(return_value=license_row),
    )

    with pytest.raises(
        ConflictError,
        match="Tenant entitlement is disabled",
    ):
        await license_service.assert_feature_entitlement(
            db,
            tenant_id="tenant-1",
            feature_code="tool:send_email",
        )


@pytest.mark.asyncio
async def test_registry_assigns_commercial_entitlement_codes():
    assert registry.get("calculator").entitlement_code is None
    assert registry.get("current_time").entitlement_code is None
    assert registry.get("send_email").entitlement_code == "tool:send_email"
    assert registry.get("sales_forecast").entitlement_code == "tool:sales_forecast"


@pytest.mark.asyncio
async def test_registry_checks_feature_entitlement_when_tenant_context_exists(monkeypatch):
    check = AsyncMock()
    monkeypatch.setattr(
        license_service,
        "assert_feature_entitlement",
        check,
    )

    class _ToolDB:
        pass

    db = _ToolDB()

    async def fake_forecast(*_args, **_kwargs):
        return {"forecast": "stubbed"}

    monkeypatch.setattr(
        "app.services.sales_service.simple_forecast",
        fake_forecast,
    )

    result = await registry.execute(
        "sales_forecast",
        {"horizon_days": 30},
        permissions={"run.execute"},
        allowed_tools={"sales_forecast"},
        db=db,
        tenant_id="tenant-1",
    )

    assert result == {"forecast": "stubbed"}
    check.assert_awaited_once()
    assert check.await_args.kwargs == {
        "tenant_id": "tenant-1",
        "feature_code": "tool:sales_forecast",
    }


@pytest.mark.asyncio
async def test_registry_keeps_legacy_local_execution_without_db_context():
    result = await registry.execute(
        "calculator",
        {"expression": "2 + 2"},
        permissions={"run.execute"},
    )
    assert result["result"] == 4


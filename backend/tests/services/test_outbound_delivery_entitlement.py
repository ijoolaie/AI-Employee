from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, TenantInactiveError
from app.services import billing_service


class _Result:
    def __init__(self, row):
        self.row = row

    def scalar_one_or_none(self):
        return self.row


class _DB:
    async def execute(self, *_args, **_kwargs):
        return _Result(SimpleNamespace(status="active"))


@pytest.mark.asyncio
async def test_outbound_delivery_entitlement_reuses_run_guard_and_fails_closed(monkeypatch):
    tenant_id = uuid4()
    guard = AsyncMock(side_effect=ConflictError("subscription expired"))
    monkeypatch.setattr(billing_service, "assert_run_execution_entitlement", guard)

    with pytest.raises(TenantInactiveError, match="Commercial entitlement is inactive"):
        await billing_service.assert_outbound_delivery_entitlement(_DB(), tenant_id=tenant_id)

    guard.assert_awaited_once()
    assert guard.await_args.kwargs == {"tenant_id": tenant_id}


@pytest.mark.asyncio
async def test_outbound_delivery_entitlement_rejects_inactive_tenant_before_commercial_lookup(monkeypatch):
    class _InactiveDB:
        async def execute(self, *_args, **_kwargs):
            return _Result(SimpleNamespace(status="suspended"))

    guard = AsyncMock()
    monkeypatch.setattr(billing_service, "assert_run_execution_entitlement", guard)

    with pytest.raises(TenantInactiveError, match="Tenant is not active"):
        await billing_service.assert_outbound_delivery_entitlement(_InactiveDB(), tenant_id=uuid4())

    guard.assert_not_awaited()

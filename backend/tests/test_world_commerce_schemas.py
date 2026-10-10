"""Validation tests for World Mode commerce request contracts."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from uuid import uuid4
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1 import world_commerce
from app.api.v1.world_commerce import feature_access, vendor_tenant_diagnostics
from app.schemas.world_commerce import WorldOrderCreateRequest, WorldPaymentSubmission
from app.services.world_commerce_service import approve_payment, create_order, mark_fulfilled


def test_order_request_accepts_supported_currency_and_no_client_price():
    request = WorldOrderCreateRequest(
        item_code="room.starter",
        currency="IRR",
        payment_method="manual_transfer",
        payment_provider="manual",
        idempotency_key="client-order-001",
    )
    assert request.currency == "IRR"
    assert not hasattr(request, "amount")


@pytest.mark.parametrize("currency", ["EUR", "BTC", "RIAL", ""])
def test_order_request_rejects_unsupported_currency(currency):
    with pytest.raises(ValidationError):
        WorldOrderCreateRequest(
            item_code="room.starter",
            currency=currency,
            payment_method="manual_transfer",
            payment_provider="manual",
            idempotency_key="client-order-002",
        )


def test_order_request_rejects_client_supplied_price_or_tenant():
    with pytest.raises(ValidationError):
        WorldOrderCreateRequest(
            item_code="room.starter",
            currency="USD",
            payment_method="gateway",
            payment_provider="example",
            idempotency_key="client-order-003",
            amount="0.01",
            tenant_id="00000000-0000-0000-0000-000000000001",
        )


def test_payment_submission_rejects_extra_verification_claims():
    with pytest.raises(ValidationError):
        WorldPaymentSubmission(
            provider_transaction_ref="reference-123",
            verified=True,
            approved_by="customer",
        )


@pytest.mark.asyncio
async def test_world_credit_is_blocked_until_wallet_ledger_exists():
    tenant_id = uuid4()
    buyer = SimpleNamespace(tenant_id=tenant_id, id=uuid4())
    with pytest.raises(HTTPException) as exc:
        await create_order(
            object(),
            tenant_id=tenant_id,
            buyer=buyer,
            item_code="room.starter",
            currency="WORLD_CREDIT",
            payment_method="world_credit",
            payment_provider="internal",
            idempotency_key="world-credit-disabled",
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_approval_blocks_unverified_gateway_payment():
    order = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), status="payment_submitted",
        payment_method="gateway",
    )
    db = AsyncMock()
    db.scalar.return_value = order
    with pytest.raises(HTTPException) as exc:
        await approve_payment(
            db, order_id=order.id, tenant_id=order.tenant_id,
            approver=SimpleNamespace(id=uuid4(), email="vendor@example.test"),
        )
    assert exc.value.status_code == 409
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_activator_must_differ_from_payment_approver():
    actor_id = uuid4()
    order = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), status="approved",
        approved_by_user_id=actor_id,
    )
    db = AsyncMock()
    db.scalar.return_value = order
    with pytest.raises(HTTPException) as exc:
        await mark_fulfilled(
            db, order_id=order.id, tenant_id=order.tenant_id,
            activator=SimpleNamespace(id=actor_id, email="vendor@example.test"),
        )
    assert exc.value.status_code == 409
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_gets_included_access_to_customization_items():
    item = SimpleNamespace(code="layout.modern", is_active=True, is_free=False, item_type="layout")
    db = AsyncMock()
    db.scalar.return_value = item
    ctx = SimpleNamespace(tenant_id=uuid4(), tenant=SimpleNamespace(tenant_kind="vendor"))
    result = await feature_access("layout.modern", ctx, db)
    assert result.data.granted is True
    assert result.data.access_source == "vendor_included"


@pytest.mark.asyncio
async def test_vendor_does_not_get_room_rental_for_free():
    item = SimpleNamespace(code="room.executive", is_active=True, is_free=False, item_type="room")
    db = AsyncMock()
    db.scalar.side_effect = [item, None]
    ctx = SimpleNamespace(tenant_id=uuid4(), tenant=SimpleNamespace(tenant_kind="vendor"))
    result = await feature_access("room.executive", ctx, db)
    assert result.data.granted is False
    assert result.data.access_source == "not_entitled"


@pytest.mark.asyncio
async def test_vendor_support_diagnostics_requires_explicit_permission(monkeypatch):
    async def deny_permission(_ctx, _permission):
        return False

    monkeypatch.setattr(world_commerce, "has_permission", deny_permission)
    ctx = SimpleNamespace(
        user=SimpleNamespace(is_platform_admin=False, id=uuid4(), email="support@example.test"),
        tenant=SimpleNamespace(tenant_kind="vendor"),
        tenant_id=uuid4(),
    )
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await vendor_tenant_diagnostics(uuid4(), ctx, db)
    assert exc.value.status_code == 403
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_support_diagnostics_cannot_access_unrelated_tenant(monkeypatch):
    async def allow_permission(_ctx, _permission):
        return True

    monkeypatch.setattr(world_commerce, "has_permission", allow_permission)
    root_id = uuid4()
    unrelated_tenant_id = uuid4()
    ctx = SimpleNamespace(
        user=SimpleNamespace(is_platform_admin=False, id=uuid4(), email="support@example.test"),
        tenant=SimpleNamespace(tenant_kind="vendor"),
        tenant_id=root_id,
    )
    result = SimpleNamespace(all=lambda: [(root_id,)])
    db = AsyncMock()
    db.execute.return_value = result
    with pytest.raises(HTTPException) as exc:
        await vendor_tenant_diagnostics(unrelated_tenant_id, ctx, db)
    assert exc.value.status_code == 404
    db.execute.assert_awaited_once()



def test_support_diagnostics_order_summary_omits_buyer_and_payment_reference():
    from app.schemas.world_commerce import WorldSupportOrderSummary

    order_id = uuid4()
    summary = WorldSupportOrderSummary(
        id=order_id,
        item_code_snapshot="room.executive",
        amount="12.50",
        currency="USD",
        status="payment_submitted",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        buyer_user_id=uuid4(),
        provider_transaction_ref="private-payment-reference",
    )
    data = summary.model_dump()
    assert "buyer_user_id" not in data
    assert "provider_transaction_ref" not in data
    assert data["id"] == order_id


@pytest.mark.asyncio
async def test_successful_vendor_diagnostics_records_audit_and_returns_minimal_data(monkeypatch):
    async def allow_permission(_ctx, _permission):
        return True

    monkeypatch.setattr(world_commerce, "has_permission", allow_permission)
    audit = AsyncMock()
    monkeypatch.setattr(world_commerce.commerce, "record_support_diagnostics_view", audit)

    tenant_id = uuid4()
    ctx = SimpleNamespace(
        user=SimpleNamespace(is_platform_admin=False, id=uuid4(), email="support@example.test"),
        tenant=SimpleNamespace(tenant_kind="vendor"),
        tenant_id=tenant_id,
    )
    scope_result = SimpleNamespace(all=lambda: [(tenant_id,)])
    count_result = SimpleNamespace(all=lambda: [("pending_payment", 2), ("fulfilled", 1)])
    order_rows = SimpleNamespace(all=lambda: [])
    entitlement_rows = SimpleNamespace(all=lambda: [])
    db = AsyncMock()
    db.execute.side_effect = [scope_result, count_result]
    db.scalar.return_value = 0
    db.scalars.side_effect = [order_rows, entitlement_rows]

    result = await vendor_tenant_diagnostics(tenant_id, ctx, db)

    assert result.data.tenant_id == tenant_id
    assert result.data.order_counts_by_status == {"pending_payment": 2, "fulfilled": 1}
    assert result.data.recent_orders == []
    assert result.data.entitlements == []
    audit.assert_awaited_once_with(
        db, tenant_id=tenant_id, actor=ctx.user, is_platform_admin=False
    )
    db.commit.assert_awaited_once()

"""Validation tests for World Mode commerce request contracts."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from uuid import uuid4
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.world_commerce import feature_access
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

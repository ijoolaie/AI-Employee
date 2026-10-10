"""Validation tests for World Mode commerce request contracts."""
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from uuid import uuid4
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1 import world_commerce
from app.api.v1.world_commerce import feature_access, vendor_tenant_diagnostics
from app.schemas.world_commerce import WorldOrderCreateRequest, WorldPaymentSubmission
from app.services.world_commerce_service import approve_payment, create_order, mark_fulfilled, submit_payment


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


def test_catalogue_admin_requires_positive_price_and_supported_choices():
    from app.schemas.world_commerce import WorldCatalogueAdminWriteRequest

    payload = WorldCatalogueAdminWriteRequest(
        code="room.starter",
        item_type="room",
        name="Starter Room",
        price_options={
            "IRR": {
                "amount": "2500000",
                "providers": ["manual"],
                "payment_methods": ["manual_transfer"],
            },
            "USD": {
                "amount": "19.99",
                "providers": ["example_gateway"],
                "payment_methods": ["gateway"],
            },
        },
    )
    assert payload.price_options["IRR"].amount == Decimal("2500000")
    assert set(payload.price_options) == {"IRR", "USD"}


def test_catalogue_admin_rejects_free_item_with_prices():
    from app.schemas.world_commerce import WorldCatalogueAdminWriteRequest

    with pytest.raises(ValidationError):
        WorldCatalogueAdminWriteRequest(
            code="room.free",
            item_type="room",
            name="Free Room",
            is_free=True,
            price_options={
                "IRR": {
                    "amount": "1",
                    "providers": ["manual"],
                    "payment_methods": ["manual_transfer"],
                }
            },
        )


def test_catalogue_admin_rejects_paid_item_without_price_options():
    from app.schemas.world_commerce import WorldCatalogueAdminWriteRequest

    with pytest.raises(ValidationError):
        WorldCatalogueAdminWriteRequest(
            code="room.missing-price",
            item_type="room",
            name="Missing Price",
        )


@pytest.mark.parametrize("option", [
    {"amount": "0", "providers": ["manual"], "payment_methods": ["manual_transfer"]},
    {"amount": "10", "providers": [], "payment_methods": ["manual_transfer"]},
    {"amount": "10", "providers": ["manual"], "payment_methods": ["world_credit"]},
    {"amount": "10", "providers": ["manual", "manual"], "payment_methods": ["manual_transfer"]},
])
def test_catalogue_admin_rejects_invalid_price_options(option):
    from app.schemas.world_commerce import WorldCatalogueAdminWriteRequest

    with pytest.raises(ValidationError):
        WorldCatalogueAdminWriteRequest(
            code="room.invalid",
            item_type="room",
            name="Invalid",
            price_options={"IRR": option},
        )


def test_catalogue_admin_rejects_unsupported_currency_and_extra_fields():
    from app.schemas.world_commerce import WorldCatalogueAdminWriteRequest

    base = {
        "code": "room.invalid",
        "item_type": "room",
        "name": "Invalid",
        "price_options": {
            "IRR": {
                "amount": "100",
                "providers": ["manual"],
                "payment_methods": ["manual_transfer"],
            }
        },
    }
    with pytest.raises(ValidationError):
        WorldCatalogueAdminWriteRequest(**{**base, "price_options": {"EUR": base["price_options"]["IRR"]}})
    with pytest.raises(ValidationError):
        WorldCatalogueAdminWriteRequest(**{**base, "tenant_id": "attacker-controlled"})

@pytest.mark.asyncio
async def test_create_order_uses_server_catalogue_price(monkeypatch):
    from app.services import world_commerce_service as commerce

    tenant_id = uuid4()
    buyer = SimpleNamespace(tenant_id=tenant_id, id=uuid4(), email="buyer@example.test")
    item = SimpleNamespace(
        id=uuid4(),
        code="room.starter",
        is_active=True,
        is_free=False,
        price_options={
            "USD": {
                "amount": "12.50",
                "providers": ["example_gateway"],
                "payment_methods": ["gateway"],
            }
        },
    )
    db = AsyncMock()
    db.scalar.side_effect = [None, item]
    event = AsyncMock()
    monkeypatch.setattr(commerce, "_event", event)

    order = await create_order(
        db,
        tenant_id=tenant_id,
        buyer=buyer,
        item_code="room.starter",
        currency="USD",
        payment_method="gateway",
        payment_provider="example_gateway",
        idempotency_key="order-server-price-001",
    )

    assert order.amount == Decimal("12.50")
    assert order.currency == "USD"
    assert order.tenant_id == tenant_id
    assert order.idempotency_key == "order-server-price-001"
    event.assert_awaited_once()
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_order_returns_existing_order_for_matching_idempotency_key():
    tenant_id = uuid4()
    existing = SimpleNamespace(
        tenant_id=tenant_id,
        item_code_snapshot="room.starter",
        currency="USD",
        payment_method="gateway",
        payment_provider="example_gateway",
        idempotency_key="order-retry-001",
    )
    db = AsyncMock()
    db.scalar.return_value = existing

    result = await create_order(
        db,
        tenant_id=tenant_id,
        buyer=SimpleNamespace(tenant_id=tenant_id, id=uuid4(), email="buyer@example.test"),
        item_code="room.starter",
        currency="USD",
        payment_method="gateway",
        payment_provider="example_gateway",
        idempotency_key="order-retry-001",
    )

    assert result is existing
    db.flush.assert_not_awaited()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_rejects_reused_idempotency_key_with_different_inputs():
    tenant_id = uuid4()
    existing = SimpleNamespace(
        tenant_id=tenant_id,
        item_code_snapshot="room.starter",
        currency="IRR",
        payment_method="manual_transfer",
        payment_provider="manual",
        idempotency_key="order-retry-conflict",
    )
    db = AsyncMock()
    db.scalar.return_value = existing

    with pytest.raises(HTTPException) as exc:
        await create_order(
            db,
            tenant_id=tenant_id,
            buyer=SimpleNamespace(tenant_id=tenant_id, id=uuid4(), email="buyer@example.test"),
            item_code="room.starter",
            currency="USD",
            payment_method="gateway",
            payment_provider="example_gateway",
            idempotency_key="order-retry-conflict",
        )

    assert exc.value.status_code == 409
    db.flush.assert_not_awaited()



@pytest.mark.asyncio
async def test_payment_reference_submission_is_only_a_claim_not_payment_approval(monkeypatch):
    from app.services import world_commerce_service as commerce

    buyer_id = uuid4()
    order = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        buyer_user_id=buyer_id,
        status="pending_payment",
        payment_provider="manual",
        provider_transaction_ref=None,
        payment_submitted_at=None,
    )
    db = AsyncMock()
    db.scalar.return_value = order
    event = AsyncMock()
    monkeypatch.setattr(commerce, "_event", event)

    result = await submit_payment(
        db,
        order_id=order.id,
        tenant_id=order.tenant_id,
        actor=SimpleNamespace(id=buyer_id, email="buyer@example.test"),
        provider_transaction_ref="  transfer-reference-123  ",
    )

    assert result is order
    assert order.provider_transaction_ref == "transfer-reference-123"
    assert order.status == "payment_submitted"
    assert not hasattr(order, "approved_at")
    assert not hasattr(order, "activated_at")
    db.flush.assert_awaited_once()
    event.assert_awaited_once()
    assert event.await_args.kwargs["event_type"] == "payment_submitted"
    assert event.await_args.kwargs["to_status"] == "payment_submitted"


@pytest.mark.asyncio
async def test_payment_reference_submission_is_restricted_to_order_buyer():
    buyer_id = uuid4()
    order = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        buyer_user_id=buyer_id,
        status="pending_payment",
        payment_provider="manual",
        provider_transaction_ref=None,
        payment_submitted_at=None,
    )
    db = AsyncMock()
    db.scalar.return_value = order

    with pytest.raises(HTTPException) as exc:
        await submit_payment(
            db,
            order_id=order.id,
            tenant_id=order.tenant_id,
            actor=SimpleNamespace(id=uuid4(), email="other@example.test"),
            provider_transaction_ref="transfer-reference-123",
        )

    assert exc.value.status_code == 403
    assert order.status == "pending_payment"
    assert order.provider_transaction_ref is None
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("payment_method", ["gateway", "crypto"])
async def test_approve_payment_blocks_unverified_non_manual_provider_methods(monkeypatch, payment_method):
    from app.services import world_commerce_service as commerce

    order = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), status="payment_submitted",
        payment_method=payment_method, approved_by_user_id=None,
        approved_at=None,
    )
    db = AsyncMock()
    db.scalar.return_value = order
    event = AsyncMock()
    monkeypatch.setattr(commerce, "_event", event)

    with pytest.raises(HTTPException) as exc:
        await commerce.approve_payment(
            db, order_id=order.id, tenant_id=order.tenant_id,
            approver=SimpleNamespace(id=uuid4(), email="reviewer@example.test"),
        )

    assert exc.value.status_code == 409
    assert "verification is not implemented" in exc.value.detail
    assert order.status == "payment_submitted"
    assert order.approved_by_user_id is None
    assert order.approved_at is None
    db.flush.assert_not_awaited()
    event.assert_not_awaited()


@pytest.mark.asyncio
async def test_approve_payment_allows_manual_transfer_review_with_audit_event(monkeypatch):
    from app.services import world_commerce_service as commerce

    approver_id = uuid4()
    order = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), status="payment_submitted",
        payment_method="manual_transfer", approved_by_user_id=None,
        approved_by_username=None, approved_at=None,
    )
    db = AsyncMock()
    db.scalar.return_value = order
    event = AsyncMock()
    monkeypatch.setattr(commerce, "_event", event)

    result = await commerce.approve_payment(
        db, order_id=order.id, tenant_id=order.tenant_id,
        approver=SimpleNamespace(id=approver_id, email="reviewer@example.test"),
    )

    assert result is order
    assert order.status == "approved"
    assert order.approved_by_user_id == approver_id
    assert order.approved_by_username == "reviewer@example.test"
    assert order.approved_at is not None
    db.flush.assert_awaited_once()
    event.assert_awaited_once()
    assert event.await_args.kwargs["event_type"] == "payment_approved"
    assert event.await_args.kwargs["from_status"] == "payment_submitted"
    assert event.await_args.kwargs["to_status"] == "approved"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["pending_payment", "payment_submitted", "rejected", "cancelled", "fulfilled"])
async def test_fulfillment_rejects_orders_not_approved(status):
    tenant_id = uuid4()
    order = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, status=status)
    db = AsyncMock()
    db.scalar.return_value = order

    with pytest.raises(HTTPException) as exc:
        await mark_fulfilled(
            db, order_id=order.id, tenant_id=tenant_id,
            activator=SimpleNamespace(id=uuid4(), email="activator@example.test"),
        )

    assert exc.value.status_code == 409
    assert "Only approved orders can be activated" in exc.value.detail
    db.add.assert_not_called()
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_fulfillment_requires_a_different_user_than_payment_approver():
    user_id = uuid4()
    tenant_id = uuid4()
    order = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, status="approved",
        approved_by_user_id=user_id,
    )
    db = AsyncMock()
    db.scalar.return_value = order

    with pytest.raises(HTTPException) as exc:
        await mark_fulfilled(
            db, order_id=order.id, tenant_id=tenant_id,
            activator=SimpleNamespace(id=user_id, email="same-person@example.test"),
        )

    assert exc.value.status_code == 409
    assert "different authorized user" in exc.value.detail
    db.add.assert_not_called()
    db.flush.assert_not_awaited()

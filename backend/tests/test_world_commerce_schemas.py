"""Validation tests for World Mode commerce request contracts."""
import pytest
from types import SimpleNamespace
from uuid import uuid4
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.world_commerce import WorldOrderCreateRequest, WorldPaymentSubmission
from app.services.world_commerce_service import create_order


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

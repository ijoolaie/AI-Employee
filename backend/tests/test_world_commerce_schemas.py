"""Validation tests for World Mode commerce request contracts."""
import pytest
from pydantic import ValidationError

from app.schemas.world_commerce import WorldOrderCreateRequest, WorldPaymentSubmission


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

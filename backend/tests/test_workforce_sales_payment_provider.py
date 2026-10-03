import uuid
from decimal import Decimal

import pytest

from app.core.config import get_settings
from app.services import workforce_sales_payment_provider


@pytest.mark.asyncio
async def test_sales_payment_provider_fails_closed_when_none(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "sales_payment_provider_name", "none")

    result = await workforce_sales_payment_provider.create_sales_checkout_session(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        deal_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        amount=Decimal("100.00"),
        currency="USD",
        customer_email="customer@example.test",
        idempotency_key="commercial-none-1",
    )

    assert result.provider_execution == "not_configured"
    assert result.executed is False
    assert result.checkout_url is None


@pytest.mark.asyncio
async def test_sales_payment_contract_test_is_deterministic_and_non_external(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "sales_payment_provider_name", "contract-test")

    deal_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    result = await workforce_sales_payment_provider.create_sales_checkout_session(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        deal_id=deal_id,
        amount=Decimal("100.00"),
        currency="USD",
        customer_email="customer@example.test",
        idempotency_key="commercial-contract-1",
    )

    assert result.provider == "contract-test"
    assert result.provider_execution == "accepted"
    assert result.executed is False
    assert result.checkout_url.endswith("/commercial-contract-1")
    assert result.provider_payment_id == f"contract-payment-{deal_id}"


@pytest.mark.asyncio
async def test_sales_payment_stripe_fails_closed_without_configuration(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "sales_payment_provider_name", "stripe")
    monkeypatch.setattr(settings, "stripe_secret_key", None)
    monkeypatch.setattr(settings, "stripe_webhook_secret", None)

    with pytest.raises(Exception, match="requires Stripe configuration"):
        await workforce_sales_payment_provider.create_sales_checkout_session(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            deal_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            amount=Decimal("100.00"),
            currency="USD",
            customer_email="customer@example.test",
            idempotency_key="commercial-stripe-1",
        )

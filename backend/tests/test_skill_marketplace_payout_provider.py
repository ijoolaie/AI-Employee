"""Focused contract tests for the governed marketplace payout provider boundary."""

from decimal import Decimal
import uuid
from types import SimpleNamespace

import pytest

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services.skill_marketplace_payout_provider import (
    ContractTestMarketplacePayoutProvider,
    MarketplacePayoutRequest,
    MarketplacePayoutStatus,
    NoneMarketplacePayoutProvider,
    StripeConnectMarketplacePayoutProvider,
    get_marketplace_payout_provider,
)


def request(**overrides):
    values = {
        "proposal_id": uuid.uuid4(),
        "settlement_id": uuid.uuid4(),
        "seller_tenant_id": uuid.uuid4(),
        "amount": Decimal("12.34"),
        "currency": "EUR",
        "destination_ref": "seller-destination-1",
        "idempotency_key": "w16-contract-payout-1",
    }
    values.update(overrides)
    return MarketplacePayoutRequest(**values)


@pytest.mark.asyncio
async def test_none_provider_fails_closed():
    result = await NoneMarketplacePayoutProvider().create_payout(request())
    assert result.provider == "none"
    assert result.status == MarketplacePayoutStatus.NOT_CONFIGURED
    assert result.provider_execution == "not_configured"
    assert result.executed is False
    assert result.external_execution is False
    assert result.failure_code == "provider_not_configured"


@pytest.mark.asyncio
async def test_contract_test_provider_is_deterministic_and_non_external():
    provider = ContractTestMarketplacePayoutProvider()
    first = await provider.create_payout(request())
    second = await provider.create_payout(request())

    assert first.provider == "contract-test"
    assert first.status == MarketplacePayoutStatus.ACCEPTED
    assert first.provider_execution == "simulated"
    assert first.executed is False
    assert first.external_execution is False
    assert first.provider_payout_id == second.provider_payout_id
    assert first.provider_event_id == second.provider_event_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount", Decimal("0")),
        ("currency", "EU"),
        ("destination_ref", " "),
        ("idempotency_key", ""),
    ],
)
async def test_provider_rejects_invalid_payout_request(field, value):
    values = {field: value}
    with pytest.raises(ValidationAppError):
        await ContractTestMarketplacePayoutProvider().create_payout(request(**values))


def test_provider_selection_is_operator_configured_and_fail_closed():
    settings = get_settings()
    original = settings.marketplace_payout_provider_name
    try:
        settings.marketplace_payout_provider_name = "contract-test"
        assert isinstance(get_marketplace_payout_provider(), ContractTestMarketplacePayoutProvider)

        settings.marketplace_payout_provider_name = "none"
        assert isinstance(get_marketplace_payout_provider(), NoneMarketplacePayoutProvider)

        settings.marketplace_payout_provider_name = "http"
        with pytest.raises(ValidationAppError):
            get_marketplace_payout_provider()
    finally:
        settings.marketplace_payout_provider_name = original


@pytest.mark.asyncio
async def test_stripe_connect_provider_submits_idempotent_transfer(monkeypatch):
    settings = get_settings()
    original_key = settings.stripe_secret_key
    settings.stripe_secret_key = "sk_test_operator_configured"
    calls = []

    class Transfer:
        @staticmethod
        def create(**kwargs):
            calls.append(kwargs)
            return type("TransferResult", (), {"id": "tr_test_123"})()

    fake_stripe = type("Stripe", (), {"Transfer": Transfer})
    monkeypatch.setattr("app.services.skill_marketplace_payout_provider._stripe_client", lambda: fake_stripe)
    try:
        result = await StripeConnectMarketplacePayoutProvider().create_payout(
            request(destination_ref="acct_123", currency="EUR", amount=Decimal("12.34"))
        )
    finally:
        settings.stripe_secret_key = original_key

    assert result.status == MarketplacePayoutStatus.ACCEPTED
    assert result.provider == "stripe-connect"
    assert result.provider_execution == "submitted"
    assert result.executed is True
    assert result.external_execution is True
    assert result.provider_payout_id == "tr_test_123"
    assert result.provider_event_id == "tr_test_123"
    assert calls[0]["amount"] == 1234
    assert calls[0]["currency"] == "eur"
    assert calls[0]["destination"] == "acct_123"
    assert calls[0]["idempotency_key"] == "w16-contract-payout-1"


@pytest.mark.asyncio
async def test_stripe_connect_rejects_non_account_destination(monkeypatch):
    monkeypatch.setattr("app.services.skill_marketplace_payout_provider._stripe_client", lambda: object())
    with pytest.raises(ValidationAppError):
        await StripeConnectMarketplacePayoutProvider().create_payout(request(destination_ref="seller-destination-1"))


def test_stripe_connect_provider_is_named_and_operator_selected():
    settings = get_settings()
    original_provider = settings.marketplace_payout_provider_name
    original_key = settings.stripe_secret_key
    try:
        settings.marketplace_payout_provider_name = "stripe-connect"
        settings.stripe_secret_key = "sk_test_operator_configured"
        assert isinstance(get_marketplace_payout_provider(), StripeConnectMarketplacePayoutProvider)
    finally:
        settings.marketplace_payout_provider_name = original_provider
        settings.stripe_secret_key = original_key


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_name", "expected_status", "expected_retryable"),
    [
        ("APIConnectionError", MarketplacePayoutStatus.UNKNOWN, True),
        ("RateLimitError", MarketplacePayoutStatus.UNKNOWN, True),
        ("APIError", MarketplacePayoutStatus.UNKNOWN, True),
        ("InvalidRequestError", MarketplacePayoutStatus.FAILED, False),
    ],
)
async def test_stripe_connect_maps_provider_errors_to_durable_states(
    monkeypatch, error_name, expected_status, expected_retryable
):
    error_classes = {
        name: type(name, (Exception,), {})
        for name in ("APIConnectionError", "RateLimitError", "APIError", "InvalidRequestError")
    }
    error_type = error_classes[error_name]

    class Transfer:
        @staticmethod
        def create(**kwargs):
            raise error_type("simulated")

    fake_stripe = type(
        "Stripe",
        (),
        {
            "Transfer": Transfer,
            "error": SimpleNamespace(**error_classes),
        },
    )
    monkeypatch.setattr(
        "app.services.skill_marketplace_payout_provider._stripe_client",
        lambda: fake_stripe,
    )

    result = await StripeConnectMarketplacePayoutProvider().create_payout(
        request(destination_ref="acct_123")
    )

    assert result.status == expected_status
    assert result.failure_code == error_name
    assert result.retryable is expected_retryable
    assert result.executed is False
    assert result.external_execution is False
    assert result.provider == "stripe-connect"
    assert result.provider_execution == (
        "ambiguous" if expected_status == MarketplacePayoutStatus.UNKNOWN else "rejected"
    )

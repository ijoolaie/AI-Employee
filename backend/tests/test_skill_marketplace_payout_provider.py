"""Focused contract tests for the governed marketplace payout provider boundary."""

from decimal import Decimal
import uuid

import pytest

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services.skill_marketplace_payout_provider import (
    ContractTestMarketplacePayoutProvider,
    MarketplacePayoutRequest,
    MarketplacePayoutStatus,
    NoneMarketplacePayoutProvider,
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

import pytest

from app.services.skill_marketplace_payout_provider import (
    ContractTestMarketplacePayoutProvider,
    HttpMarketplacePayoutProvider,
    MarketplacePayoutProviderUnknown,
    UnconfiguredMarketplacePayoutProvider,
    get_marketplace_payout_provider,
)


def test_default_payout_provider_is_fail_closed():
    provider = UnconfiguredMarketplacePayoutProvider()
    assert provider.name == "none"
    assert provider.external_execution is False


def test_contract_test_provider_executes_deterministically():
    result = ContractTestMarketplacePayoutProvider().execute(
        proposal_id="proposal-1",
        seller_tenant_id="seller-1",
        destination="seller-destination",
        amount="10.00",
        currency="EUR",
        idempotency_key="marketplace-payout:proposal-1",
    )
    assert result.executed is True
    assert result.provider_payout_id == "contract-payout-proposal-1"


def test_http_provider_is_external():
    assert HttpMarketplacePayoutProvider.external_execution is True


def test_unknown_provider_name_fails_closed(monkeypatch):
    import app.core.config as config
    monkeypatch.setattr(config.get_settings(), "skill_marketplace_payout_provider_name", "shell")
    with pytest.raises(ValueError, match="Unknown marketplace payout provider"):
        get_marketplace_payout_provider()


def test_unknown_outcome_type_is_distinct():
    assert MarketplacePayoutProviderUnknown.__name__ == "MarketplacePayoutProviderUnknown"

"""Named provider boundary for governed marketplace seller payouts.

The governed payout service selects only operator-configured named adapters.
The Stripe Connect adapter is the only real external payout transport in this
boundary; credentials remain operator-owned and runtime data cannot select a
provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
import uuid
from typing import Protocol

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError


class MarketplacePayoutStatus(StrEnum):
    NOT_CONFIGURED = "not_configured"
    ACCEPTED = "accepted"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MarketplacePayoutRequest:
    proposal_id: uuid.UUID
    settlement_id: uuid.UUID
    seller_tenant_id: uuid.UUID
    amount: Decimal
    currency: str
    destination_ref: str
    idempotency_key: str


@dataclass(frozen=True)
class MarketplacePayoutResult:
    provider: str
    status: MarketplacePayoutStatus
    provider_execution: str
    executed: bool
    external_execution: bool
    provider_payout_id: str | None
    provider_event_id: str | None
    failure_code: str | None = None
    retryable: bool = False


class MarketplacePayoutProvider(Protocol):
    async def create_payout(
        self,
        request: MarketplacePayoutRequest,
    ) -> MarketplacePayoutResult:
        """Create or submit one idempotent seller payout request."""


def _validate_request(request: MarketplacePayoutRequest) -> None:
    if request.amount <= 0:
        raise ValidationAppError("Marketplace payout amount must be positive")
    if len(request.currency) != 3 or not request.currency.isalpha():
        raise ValidationAppError("Marketplace payout currency must be a three-letter ISO currency")
    if not request.destination_ref.strip():
        raise ValidationAppError("Marketplace payout destination is required")
    if not request.idempotency_key.strip():
        raise ValidationAppError("Marketplace payout idempotency key is required")


class NoneMarketplacePayoutProvider:
    """Fail-closed provider used when no payout provider is configured."""

    name = "none"

    async def create_payout(
        self,
        request: MarketplacePayoutRequest,
    ) -> MarketplacePayoutResult:
        _validate_request(request)
        return MarketplacePayoutResult(
            provider=self.name,
            status=MarketplacePayoutStatus.NOT_CONFIGURED,
            provider_execution="not_configured",
            executed=False,
            external_execution=False,
            provider_payout_id=None,
            provider_event_id=None,
            failure_code="provider_not_configured",
            retryable=False,
        )


class ContractTestMarketplacePayoutProvider:
    """Deterministic test adapter; it never calls an external service."""

    name = "contract-test"

    async def create_payout(
        self,
        request: MarketplacePayoutRequest,
    ) -> MarketplacePayoutResult:
        _validate_request(request)
        payout_id = f"contract-payout-{request.idempotency_key}"
        event_id = f"contract-payout-event-{request.idempotency_key}"
        return MarketplacePayoutResult(
            provider=self.name,
            status=MarketplacePayoutStatus.ACCEPTED,
            provider_execution="simulated",
            executed=False,
            external_execution=False,
            provider_payout_id=payout_id,
            provider_event_id=event_id,
            failure_code=None,
            retryable=False,
        )


ZERO_DECIMAL_CURRENCIES = {
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga",
    "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf",
}


def _stripe_client():
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise ValidationAppError(
            "Stripe Connect payout provider is not configured: STRIPE_SECRET_KEY is required"
        )
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


def _minor_units(amount: Decimal, currency: str) -> int:
    normalized = currency.lower()
    quantum = Decimal("1") if normalized in ZERO_DECIMAL_CURRENCIES else Decimal("0.01")
    minor = (amount / quantum).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if minor <= 0:
        raise ValidationAppError("Marketplace payout amount rounds to zero provider units")
    return int(minor)


class StripeConnectMarketplacePayoutProvider:
    """Stripe Connect transfer adapter with provider-side idempotency."""

    name = "stripe-connect"

    async def create_payout(
        self,
        request: MarketplacePayoutRequest,
    ) -> MarketplacePayoutResult:
        _validate_request(request)
        destination = request.destination_ref.strip()
        if not destination.startswith("acct_"):
            raise ValidationAppError(
                "Stripe Connect destination must be an account reference beginning with acct_"
            )
        stripe = _stripe_client()
        try:
            transfer = stripe.Transfer.create(
                amount=_minor_units(request.amount, request.currency),
                currency=request.currency.lower(),
                destination=destination,
                metadata={
                    "marketplace_payout_proposal_id": str(request.proposal_id),
                    "marketplace_settlement_id": str(request.settlement_id),
                    "seller_tenant_id": str(request.seller_tenant_id),
                },
                idempotency_key=request.idempotency_key,
            )
        except Exception as exc:
            if isinstance(
                exc,
                (
                    stripe.error.APIConnectionError,
                    stripe.error.RateLimitError,
                    stripe.error.APIError,
                ),
            ):
                return MarketplacePayoutResult(
                    provider=self.name,
                    status=MarketplacePayoutStatus.UNKNOWN,
                    provider_execution="ambiguous",
                    executed=False,
                    external_execution=False,
                    provider_payout_id=None,
                    provider_event_id=None,
                    failure_code=exc.__class__.__name__,
                    retryable=True,
                )
            if isinstance(exc, stripe.error.InvalidRequestError):
                return MarketplacePayoutResult(
                    provider=self.name,
                    status=MarketplacePayoutStatus.FAILED,
                    provider_execution="rejected",
                    executed=False,
                    external_execution=False,
                    provider_payout_id=None,
                    provider_event_id=None,
                    failure_code=exc.__class__.__name__,
                    retryable=False,
                )
            raise
        transfer_id = str(transfer.id)
        return MarketplacePayoutResult(
            provider=self.name,
            status=MarketplacePayoutStatus.ACCEPTED,
            provider_execution="submitted",
            executed=True,
            external_execution=True,
            provider_payout_id=transfer_id,
            provider_event_id=transfer_id,
            failure_code=None,
            retryable=False,
        )


def get_marketplace_payout_provider() -> MarketplacePayoutProvider:
    """Resolve the operator-selected named adapter.

    Runtime request data cannot select the provider. Unknown providers fail
    closed instead of falling back to an arbitrary transport.
    """

    provider = get_settings().marketplace_payout_provider_name.lower().strip()
    if provider == "none":
        return NoneMarketplacePayoutProvider()
    if provider == "contract-test":
        return ContractTestMarketplacePayoutProvider()
    if provider == "stripe-connect":
        return StripeConnectMarketplacePayoutProvider()
    raise ValidationAppError(f"Unsupported marketplace payout provider: {provider}")

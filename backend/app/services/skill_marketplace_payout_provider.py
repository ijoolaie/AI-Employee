"""Provider contract for governed marketplace seller payouts.

This module defines the provider boundary only. It does not execute a payout
from the marketplace proposal flow. External providers must be added as named
adapters with operator-owned configuration and explicit side-effect semantics.
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
        amount = request.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
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
    raise ValidationAppError(f"Unsupported marketplace payout provider: {provider}")

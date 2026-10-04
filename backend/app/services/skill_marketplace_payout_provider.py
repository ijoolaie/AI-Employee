"""Explicit external provider boundary for seller payout execution."""
from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from typing import Any

from app.core.config import get_settings


@dataclass(frozen=True)
class MarketplacePayoutResult:
    provider: str
    executed: bool
    status: str
    provider_payout_id: str | None = None


class MarketplacePayoutProviderError(RuntimeError):
    """A provider rejected a payout without an ambiguous outcome."""


class MarketplacePayoutProviderUnknown(RuntimeError):
    """Provider outcome is ambiguous; do not retry automatically."""


class MarketplacePayoutProvider:
    name = "none"
    external_execution = False

    def execute(self, **kwargs: Any) -> MarketplacePayoutResult:
        raise NotImplementedError


class UnconfiguredMarketplacePayoutProvider(MarketplacePayoutProvider):
    name = "none"

    def execute(self, **kwargs: Any) -> MarketplacePayoutResult:
        raise MarketplacePayoutProviderError(
            "No operator-configured marketplace payout provider is available"
        )


class ContractTestMarketplacePayoutProvider(MarketplacePayoutProvider):
    name = "contract-test"
    external_execution = False

    def execute(self, *, proposal_id: str, seller_tenant_id: str, destination: str, amount: str, currency: str, idempotency_key: str, **kwargs: Any) -> MarketplacePayoutResult:
        if not destination or not idempotency_key:
            raise MarketplacePayoutProviderError("contract-test payout requires destination and idempotency key")
        return MarketplacePayoutResult(
            provider=self.name,
            executed=True,
            status="executed",
            provider_payout_id=f"contract-payout-{proposal_id}",
        )


class HttpMarketplacePayoutProvider(MarketplacePayoutProvider):
    name = "http"
    external_execution = True
    MAX_RESPONSE_BYTES = 65_536

    class _NoRedirectHandler(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise MarketplacePayoutProviderError("marketplace payout provider redirects are not permitted")

    def execute(
        self,
        *,
        proposal_id: str,
        seller_tenant_id: str,
        destination: str,
        amount: str,
        currency: str,
        idempotency_key: str,
        **kwargs: Any,
    ) -> MarketplacePayoutResult:
        settings = get_settings()
        endpoint = settings.skill_marketplace_payout_provider_base_url
        api_key = settings.skill_marketplace_payout_provider_api_key
        if not endpoint or not api_key:
            raise MarketplacePayoutProviderError(
                "Marketplace payout provider endpoint or API key is not configured"
            )
        payload = json.dumps(
            {
                "proposal_id": proposal_id,
                "seller_tenant_id": seller_tenant_id,
                "destination": destination,
                "amount": amount,
                "currency": currency,
                "idempotency_key": idempotency_key,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-AI-Employee-Marketplace-Payout": "1",
            },
            method="POST",
        )
        try:
            with build_opener(self._NoRedirectHandler).open(
                request, timeout=settings.skill_marketplace_payout_provider_timeout_seconds
            ) as response:
                raw = response.read(self.MAX_RESPONSE_BYTES + 1)
                if len(raw) > self.MAX_RESPONSE_BYTES:
                    raise MarketplacePayoutProviderError(
                        "Marketplace payout provider response exceeds the configured size limit"
                    )
                data = json.loads(raw.decode("utf-8"))
        except MarketplacePayoutProviderError:
            raise
        except HTTPError as exc:
            if 400 <= exc.code < 500:
                raise MarketplacePayoutProviderError(
                    f"Marketplace payout provider rejected payout: HTTP {exc.code}"
                ) from exc
            raise MarketplacePayoutProviderUnknown(
                f"Marketplace payout provider outcome is unknown: HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, ValueError, UnicodeDecodeError) as exc:
            raise MarketplacePayoutProviderUnknown(
                f"Marketplace payout provider outcome is unknown: {type(exc).__name__}"
            ) from exc

        if not isinstance(data, dict) or data.get("accepted") is not True:
            raise MarketplacePayoutProviderError(
                "Marketplace payout provider response did not confirm acceptance"
            )
        payout_id = data.get("payout_id")
        if payout_id is not None and (not isinstance(payout_id, str) or not payout_id.strip()):
            raise MarketplacePayoutProviderError("Marketplace payout provider returned an invalid payout_id")
        return MarketplacePayoutResult(
            provider=self.name,
            executed=bool(data.get("executed") is True),
            status="executed" if data.get("executed") is True else "accepted",
            provider_payout_id=payout_id,
        )


def get_marketplace_payout_provider() -> MarketplacePayoutProvider:
    name = get_settings().skill_marketplace_payout_provider_name.strip().lower()
    if name == "none":
        return UnconfiguredMarketplacePayoutProvider()
    if name == "contract-test":
        return ContractTestMarketplacePayoutProvider()
    if name == "http":
        return HttpMarketplacePayoutProvider()
    raise ValueError(f"Unknown marketplace payout provider: {name}")

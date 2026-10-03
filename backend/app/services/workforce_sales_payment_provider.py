"""Provider boundary for governed sales commercial commitments.

Provider selection is operator-controlled. Runtime arguments cannot select a
provider. Contract-test is deterministic and never calls an external service;
Stripe creates a one-time Checkout Session with immutable deal/tenant metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import uuid

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError


@dataclass(frozen=True)
class SalesPaymentResult:
    provider: str
    provider_execution: str
    executed: bool
    checkout_url: str | None
    provider_payment_id: str | None


ZERO_DECIMAL_CURRENCIES = frozenset({"bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"})


def _minor_units(amount: Decimal, currency: str) -> int:
    multiplier = Decimal("1") if currency.lower() in ZERO_DECIMAL_CURRENCIES else Decimal("100")
    value = (amount * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if value <= 0:
        raise ValidationAppError("Commercial commitment amount must be positive")
    return int(value)




def _major_units(amount_minor: int, currency: str) -> Decimal:
    divisor = Decimal("1") if currency.lower() in ZERO_DECIMAL_CURRENCIES else Decimal("100")
    return Decimal(amount_minor) / divisor


async def create_sales_checkout_session(
    *,
    tenant_id: uuid.UUID,
    deal_id: uuid.UUID,
    amount: Decimal,
    currency: str,
    customer_email: str | None,
    idempotency_key: str,
) -> SalesPaymentResult:
    settings = get_settings()
    provider = settings.sales_payment_provider_name.lower().strip()
    if provider == "none":
        return SalesPaymentResult("none", "not_configured", False, None, None)
    if amount <= 0:
        raise ValidationAppError("Commercial commitment amount must be positive")
    currency = (currency or "usd").lower()
    if len(currency) != 3 or not currency.isalpha():
        raise ValidationAppError("Sales payment currency must be a three-letter ISO currency")
    if provider == "contract-test":
        return SalesPaymentResult(
            "contract-test",
            "accepted",
            False,
            f"https://contract-test.invalid/checkout/{deal_id}/{idempotency_key}",
            f"contract-payment-{deal_id}",
        )
    if provider != "stripe":
        raise ValidationAppError(f"Unsupported sales payment provider: {provider}")
    if not settings.stripe_secret_key:
        raise ValidationAppError("Sales payment provider stripe requires STRIPE_SECRET_KEY")

    import stripe

    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": currency,
                "unit_amount": _minor_units(amount, currency),
                "product_data": {"name": f"AI Workforce commercial commitment {deal_id}"},
            },
            "quantity": 1,
        }],
        customer_email=customer_email,
        success_url=settings.stripe_checkout_success_url,
        cancel_url=settings.stripe_checkout_cancel_url,
        client_reference_id=str(deal_id),
        metadata={"tenant_id": str(tenant_id), "sales_deal_id": str(deal_id)},
        payment_intent_data={"metadata": {"tenant_id": str(tenant_id), "sales_deal_id": str(deal_id)}},
        idempotency_key=idempotency_key,
    )
    return SalesPaymentResult(
        "stripe",
        "accepted",
        True,
        session.url,
        getattr(session, "payment_intent", None),
    )

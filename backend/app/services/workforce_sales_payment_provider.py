"""Provider boundary for governed sales commercial commitments.

Provider selection is operator-controlled. Runtime arguments cannot select a
provider. Contract-test is deterministic and never calls an external service.
Stripe and ZarinPal are explicit external adapters with tenant/deal correlation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ValidationAppError


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
    db=None,
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
    if provider == "zarinpal":
        if not settings.zarinpal_merchant_id:
            raise ValidationAppError("Sales payment provider zarinpal requires ZARINPAL_MERCHANT_ID")
        if db is None:
            raise ValidationAppError("Sales payment provider zarinpal requires an active tenant Run database context")
        from app.models.business_deal import BusinessDeal
        from app.services.zarinpal_service import create_payment_request
        deal = (
            await db.execute(
                select(BusinessDeal).where(
                    BusinessDeal.id == deal_id,
                    BusinessDeal.tenant_id == tenant_id,
                ).with_for_update()
            )
        ).scalar_one_or_none()
        if deal is None:
            raise ValidationAppError("Sales payment provider zarinpal references an unknown deal")
        metadata = dict(deal.metadata_ or {})
        if metadata.get("payment_provider") == "zarinpal":
            stored_key = metadata.get("payment_provider_idempotency_key")
            authority = metadata.get("payment_provider_authority")
            attempt_state = metadata.get("payment_attempt_state")
            if authority and stored_key == idempotency_key:
                from app.services.zarinpal_service import gateway_url
                return SalesPaymentResult(
                    "zarinpal",
                    "accepted",
                    True,
                    gateway_url(str(authority)),
                    str(authority),
                )
            if attempt_state == "pending":
                raise ConflictError(
                    "ZarinPal payment request outcome is unresolved; reconcile the existing "
                    "attempt before creating another checkout"
                )
            if authority:
                raise ConflictError("ZarinPal checkout already exists for this deal")
        # This commit is deliberate: the durable attempt marker must survive a
        # process crash after ZarinPal accepts the request but before the
        # provider authority can be persisted. A retry seeing pending must
        # reconcile instead of issuing a second provider request.
        metadata["payment_provider"] = "zarinpal"
        metadata["payment_provider_idempotency_key"] = idempotency_key
        metadata["payment_attempt_state"] = "pending"
        metadata["payment_attempt_started_at"] = datetime.now(timezone.utc).isoformat()
        metadata.pop("payment_provider_authority", None)
        deal.metadata_ = metadata
        await db.flush()
        await db.commit()
        try:
            result = await create_payment_request(
                tenant_id=tenant_id,
                deal_id=deal_id,
                amount=amount,
                currency=currency,
                customer_email=customer_email,
                idempotency_key=idempotency_key,
            )
        except Exception:
            # Keep the durable pending marker. Network failures and process
            # crashes are ambiguous at the external boundary; retrying here
            # could create a second checkout.
            raise
        persisted_deal = (
            await db.execute(
                select(BusinessDeal).where(
                    BusinessDeal.id == deal_id,
                    BusinessDeal.tenant_id == tenant_id,
                ).with_for_update()
            )
        ).scalar_one_or_none()
        if persisted_deal is None:
            raise ValidationAppError("ZarinPal checkout deal disappeared during reconciliation")
        persisted_metadata = dict(persisted_deal.metadata_ or {})
        if (
            persisted_metadata.get("payment_provider") != "zarinpal"
            or persisted_metadata.get("payment_provider_idempotency_key") != idempotency_key
            or persisted_metadata.get("payment_attempt_state") != "pending"
        ):
            raise ConflictError("ZarinPal payment attempt ownership changed during provider execution")
        persisted_metadata["payment_provider_authority"] = result.provider_payment_id
        persisted_metadata["payment_amount"] = float(amount)
        persisted_metadata["payment_currency"] = currency.upper()
        persisted_metadata["payment_attempt_state"] = "accepted"
        persisted_deal.metadata_ = persisted_metadata
        await db.flush()
        await db.commit()
        return result
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

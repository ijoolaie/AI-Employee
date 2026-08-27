"""Refund/reversal orchestration with tenant isolation and idempotency."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.billing import BillingEvent, Subscription
from app.models.refund import PaymentRefund
from app.services import stripe_service


async def _assert_payment_intent_belongs_to_tenant(
    db: AsyncSession, *, tenant_id: uuid.UUID, payment_intent_id: str
) -> dict:
    sub = (
        await db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if sub is None or sub.provider != "stripe" or not sub.provider_customer_id:
        raise ConflictError("Tenant has no Stripe customer eligible for payment reversal")

    settings = get_settings()
    if not settings.stripe_enabled:
        raise ValidationAppError("Stripe is not configured on this deployment")
    import stripe

    stripe.api_key = settings.stripe_secret_key
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    customer_id = payment_intent.get("customer")
    if customer_id != sub.provider_customer_id:
        raise ConflictError("Payment does not belong to the current tenant")
    return {
        "currency": (payment_intent.get("currency") or "usd").lower(),
        "status": payment_intent.get("status"),
    }


async def _record_lifecycle_event(
    db: AsyncSession,
    *,
    row: PaymentRefund,
    status: str,
) -> None:
    provider_event_id = f"refund-request:{row.tenant_id}:{row.idempotency_key}"
    event = (
        await db.execute(
            select(BillingEvent).where(
                BillingEvent.provider == "stripe",
                BillingEvent.provider_event_id == provider_event_id,
            )
        )
    ).scalar_one_or_none()
    payload = {
        "refund_id": str(row.id),
        "operation": row.operation,
        "payment_intent_id": row.provider_payment_intent_id,
        "provider_refund_id": row.provider_refund_id,
        "amount_cents": row.amount_cents,
        "currency": row.currency,
        "reason": row.reason,
        "failure_reason": row.failure_reason,
    }
    if event is None:
        event = BillingEvent(
            tenant_id=row.tenant_id,
            provider="stripe",
            provider_event_id=provider_event_id,
            event_type=f"payment.{row.operation}.requested",
            payload=payload,
            status=status,
        )
        db.add(event)
    else:
        event.tenant_id = row.tenant_id
        event.payload = payload
        event.status = status
    await db.flush()


async def request_refund(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    operation: str,
    payment_intent_id: str,
    amount_cents: int | None,
    currency: str,
    reason: str | None,
    idempotency_key: str,
) -> PaymentRefund:
    if operation not in {"refund", "reversal"}:
        raise ValidationAppError("Unsupported payment operation")
    if not payment_intent_id:
        raise ValidationAppError("payment_intent_id is required")
    if amount_cents is not None and amount_cents <= 0:
        raise ValidationAppError("amount_cents must be greater than zero")

    existing = (
        await db.execute(
            select(PaymentRefund).where(
                PaymentRefund.tenant_id == tenant_id,
                PaymentRefund.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        same_request = (
            existing.operation == operation
            and existing.provider_payment_intent_id == payment_intent_id
            and existing.amount_cents == amount_cents
            and existing.currency.lower() == currency.lower()
        )
        if not same_request:
            raise ConflictError("Idempotency key already belongs to a different refund request")
        if existing.status != "failed":
            return existing

    payment = await _assert_payment_intent_belongs_to_tenant(
        db, tenant_id=tenant_id, payment_intent_id=payment_intent_id
    )
    if payment["currency"] != currency.lower():
        raise ValidationAppError("Refund currency does not match the PaymentIntent currency")

    row = existing or PaymentRefund(
        tenant_id=tenant_id,
        operation=operation,
        provider="stripe",
        provider_payment_intent_id=payment_intent_id,
        amount_cents=amount_cents,
        currency=currency.lower(),
        status="pending",
        reason=reason,
        idempotency_key=idempotency_key,
    )
    row.status = "pending"
    row.failure_reason = None
    if existing is None:
        db.add(row)
    await db.flush()

    try:
        if operation == "refund":
            result = await stripe_service.create_refund(
                payment_intent_id=payment_intent_id,
                amount_cents=amount_cents,
                reason=reason,
                idempotency_key=idempotency_key,
            )
            row.provider_refund_id = result.get("id")
            row.provider_charge_id = result.get("charge")
            row.status = result.get("status") or "pending"
            row.currency = (result.get("currency") or currency).lower()
            if result.get("amount") is not None:
                row.amount_cents = int(result["amount"])
        else:
            if payment["status"] not in {"requires_capture", "requires_confirmation", "requires_action"}:
                raise ConflictError("PaymentIntent is not eligible for reversal")
            result = await stripe_service.create_reversal(
                payment_intent_id=payment_intent_id,
                idempotency_key=idempotency_key,
            )
            row.status = "succeeded" if result.get("status") == "canceled" else (result.get("status") or "pending")
            row.metadata = {
                "provider_operation": "payment_intent_cancel",
                "provider_status": result.get("status"),
            }
    except Exception as exc:
        row.status = "failed"
        row.failure_reason = str(exc)[:1000]
        await db.flush()
        await _record_lifecycle_event(db, row=row, status="failed")
        return row

    await db.flush()
    await _record_lifecycle_event(db, row=row, status="processed")
    return row


async def get_refund(db: AsyncSession, *, tenant_id: uuid.UUID, refund_id: uuid.UUID) -> PaymentRefund:
    row = (
        await db.execute(
            select(PaymentRefund).where(
                PaymentRefund.id == refund_id,
                PaymentRefund.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Refund or reversal not found")
    return row


async def reconcile_stripe_refund_event(db: AsyncSession, *, event: dict) -> PaymentRefund | None:
    data = event["data"]["object"]
    provider_refund_id = data.get("id")
    if not provider_refund_id:
        return None
    row = (
        await db.execute(
            select(PaymentRefund).where(
                PaymentRefund.provider == "stripe",
                PaymentRefund.provider_refund_id == provider_refund_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    row.status = data.get("status") or row.status
    row.failure_reason = data.get("failure_reason")
    if data.get("amount") is not None:
        row.amount_cents = int(data["amount"])
    if data.get("currency"):
        row.currency = data["currency"].lower()
    await db.flush()
    return row

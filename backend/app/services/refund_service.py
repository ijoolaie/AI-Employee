"""Refund/reversal orchestration with tenant isolation and idempotency."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.refund import PaymentRefund
from app.services import stripe_service


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
    if existing is not None and existing.status != "failed":
        return existing

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
            result = await stripe_service.create_reversal(
                payment_intent_id=payment_intent_id,
                idempotency_key=idempotency_key,
            )
            row.status = "succeeded" if result.get("status") == "canceled" else (result.get("status") or "pending")
            row.metadata = {"provider_operation": "payment_intent_cancel", "provider_status": result.get("status")}
    except Exception as exc:
        row.status = "failed"
        row.failure_reason = str(exc)[:1000]
        await db.flush()
        return row

    await db.flush()
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

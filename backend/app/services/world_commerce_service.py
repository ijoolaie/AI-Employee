"""World Mode order lifecycle helpers.

No payment provider is treated as verified here. This module records a customer
payment claim and the vendor's explicit decision; provider adapters/webhooks
must be implemented separately before any automated verification is enabled.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.world_commerce import WorldCatalogueItem, WorldCommerceEvent, WorldOrder
from app.services import audit_service

SUPPORTED_CURRENCIES = {"IRR", "USD", "USDT", "WORLD_CREDIT"}
PAYMENT_METHODS = {"manual_transfer", "gateway", "crypto", "world_credit"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _event(
    db: AsyncSession,
    *,
    order: WorldOrder,
    event_type: str,
    actor_id: UUID | None,
    actor_username: str | None,
    from_status: str | None,
    to_status: str | None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(WorldCommerceEvent(
        tenant_id=order.tenant_id,
        order_id=order.id,
        event_type=event_type,
        actor_user_id=actor_id,
        actor_username=actor_username,
        from_status=from_status,
        to_status=to_status,
        details=details or {},
    ))
    await audit_service.record(
        db,
        tenant_id=order.tenant_id,
        actor_type="user" if actor_id else "system",
        actor_id=actor_id,
        action=f"world.commerce.{event_type}",
        resource_type="world_order",
        resource_id=str(order.id),
        metadata={"from_status": from_status, "to_status": to_status, **(details or {})},
    )


async def create_order(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    buyer: User,
    item_code: str,
    currency: str,
    payment_method: str,
    payment_provider: str,
    idempotency_key: str,
) -> WorldOrder:
    """Create a pending order using only the server-side catalogue price."""
    if buyer.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Buyer tenant mismatch")
    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=422, detail="Unsupported currency")
    if payment_method not in PAYMENT_METHODS:
        raise HTTPException(status_code=422, detail="Unsupported payment method")
    if not idempotency_key or len(idempotency_key) > 128:
        raise HTTPException(status_code=422, detail="A valid idempotency key is required")

    existing = await db.scalar(select(WorldOrder).where(
        WorldOrder.tenant_id == tenant_id,
        WorldOrder.idempotency_key == idempotency_key,
    ))
    if existing:
        if (existing.item_code_snapshot != item_code or existing.currency != currency
                or existing.payment_method != payment_method or existing.payment_provider != payment_provider):
            raise HTTPException(status_code=409, detail="Idempotency key was already used for a different order")
        return existing

    item = await db.scalar(select(WorldCatalogueItem).where(
        WorldCatalogueItem.code == item_code,
        WorldCatalogueItem.is_active.is_(True),
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="World catalogue item not found")
    if item.is_free:
        raise HTTPException(status_code=409, detail="Free access must be granted through entitlements, not a paid order")

    option = (item.price_options or {}).get(currency)
    if not isinstance(option, dict):
        raise HTTPException(status_code=422, detail="This item is not priced in the selected currency")
    providers = option.get("providers", [])
    if not isinstance(providers, list) or payment_provider not in providers:
        raise HTTPException(status_code=422, detail="Payment provider is not enabled for this currency and item")
    if payment_method not in option.get("payment_methods", [payment_method]):
        raise HTTPException(status_code=422, detail="Payment method is not enabled for this currency and item")
    try:
        amount = Decimal(str(option["amount"]))
    except (KeyError, InvalidOperation, TypeError):
        raise HTTPException(status_code=503, detail="Catalogue price is not configured correctly")
    if not amount.is_finite() or amount <= 0:
        raise HTTPException(status_code=503, detail="Paid catalogue item must have a positive configured price")

    order = WorldOrder(
        tenant_id=tenant_id,
        buyer_user_id=buyer.id,
        catalogue_item_id=item.id,
        item_code_snapshot=item.code,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        payment_provider=payment_provider,
        idempotency_key=idempotency_key,
        status="pending_payment",
    )
    db.add(order)
    await db.flush()
    await _event(
        db, order=order, event_type="order_created", actor_id=buyer.id,
        actor_username=buyer.email, from_status=None, to_status=order.status,
        details={"item_code": item.code, "amount": str(amount), "currency": currency,
                 "payment_method": payment_method, "payment_provider": payment_provider},
    )
    return order


async def submit_payment(
    db: AsyncSession, *, order_id: UUID, tenant_id: UUID, actor: User,
    provider_transaction_ref: str,
) -> WorldOrder:
    order = await db.scalar(select(WorldOrder).where(
        WorldOrder.id == order_id, WorldOrder.tenant_id == tenant_id
    ).with_for_update())
    if order is None:
        raise HTTPException(status_code=404, detail="World order not found")
    if order.buyer_user_id != actor.id:
        raise HTTPException(status_code=403, detail="Only the buyer can submit payment details")
    if order.status != "pending_payment":
        raise HTTPException(status_code=409, detail="Order is not awaiting payment submission")
    ref = provider_transaction_ref.strip()
    if not ref or len(ref) > 255:
        raise HTTPException(status_code=422, detail="A valid payment reference is required")
    old_status = order.status
    order.provider_transaction_ref = ref
    order.payment_submitted_at = _utcnow()
    order.status = "payment_submitted"
    await db.flush()
    await _event(db, order=order, event_type="payment_submitted", actor_id=actor.id,
                 actor_username=actor.email, from_status=old_status, to_status=order.status,
                 details={"provider_transaction_ref": ref})
    return order


async def approve_payment(
    db: AsyncSession, *, order_id: UUID, tenant_id: UUID, approver: User,
) -> WorldOrder:
    order = await db.scalar(select(WorldOrder).where(
        WorldOrder.id == order_id, WorldOrder.tenant_id == tenant_id
    ).with_for_update())
    if order is None:
        raise HTTPException(status_code=404, detail="World order not found")
    if order.status != "payment_submitted":
        raise HTTPException(status_code=409, detail="Only submitted payments can be approved")
    old_status = order.status
    order.status = "approved"
    order.approved_by_user_id = approver.id
    order.approved_by_username = approver.email
    order.approved_at = _utcnow()
    await db.flush()
    await _event(db, order=order, event_type="payment_approved", actor_id=approver.id,
                 actor_username=approver.email, from_status=old_status, to_status=order.status)
    return order


async def reject_payment(
    db: AsyncSession, *, order_id: UUID, tenant_id: UUID, approver: User,
    reason: str,
) -> WorldOrder:
    order = await db.scalar(select(WorldOrder).where(
        WorldOrder.id == order_id, WorldOrder.tenant_id == tenant_id
    ).with_for_update())
    if order is None:
        raise HTTPException(status_code=404, detail="World order not found")
    if order.status != "payment_submitted":
        raise HTTPException(status_code=409, detail="Only submitted payments can be rejected")
    clean_reason = reason.strip()
    if not clean_reason or len(clean_reason) > 2000:
        raise HTTPException(status_code=422, detail="A rejection reason is required")
    old_status = order.status
    order.status = "rejected"
    order.rejection_reason = clean_reason
    order.approved_by_user_id = approver.id
    order.approved_by_username = approver.email
    order.approved_at = _utcnow()
    await db.flush()
    await _event(db, order=order, event_type="payment_rejected", actor_id=approver.id,
                 actor_username=approver.email, from_status=old_status, to_status=order.status,
                 details={"reason": clean_reason})
    return order


async def mark_fulfilled(
    db: AsyncSession, *, order_id: UUID, tenant_id: UUID, activator: User,
) -> WorldOrder:
    """Record activation only after approval; fulfillment side effects are separate."""
    order = await db.scalar(select(WorldOrder).where(
        WorldOrder.id == order_id, WorldOrder.tenant_id == tenant_id
    ).with_for_update())
    if order is None:
        raise HTTPException(status_code=404, detail="World order not found")
    if order.status != "approved":
        raise HTTPException(status_code=409, detail="Only approved orders can be activated")
    old_status = order.status
    order.status = "fulfilled"
    order.activated_by_user_id = activator.id
    order.activated_by_username = activator.email
    order.activated_at = _utcnow()
    await db.flush()
    await _event(db, order=order, event_type="feature_activated", actor_id=activator.id,
                 actor_username=activator.email, from_status=old_status, to_status=order.status)
    return order

"""Order Employee domain service (Phase 8).

Persists tenant business orders, analyzes order-like files, and summarizes
pipeline status. Reuses invoice money helpers for consistent tax handling.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.business_order import BusinessOrder
from app.services import audit_service, file_service, storage
from app.services.invoice_service import _compute_totals, normalize_tax_rate

ALLOWED_STATUSES = frozenset(
    {"draft", "confirmed", "processing", "shipped", "delivered", "cancelled"}
)

_AMOUNT_RE = re.compile(
    r"[\d,\.]{3,}\s?(?:ریال|تومان|﷼|\$|€|USD|IRR|EUR)\b|(?:\$|€)\s?[\d,\.]{2,}"
)
_DATE_RE = re.compile(
    r"\b(?:13|14)\d{2}[/\-]\d{1,2}[/\-]\d{1,2}\b|\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b|\b\d{1,2}[/\-]\d{1,2}[/\-]\d{4}\b"
)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_ORDER_NO_RE = re.compile(
    r"(?:order|po|سفارش|شماره)\s*[:#]?\s*([A-Za-z0-9\-/]{3,32})",
    re.IGNORECASE,
)


def _next_number_fallback() -> str:
    return f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


async def create_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    customer_name: str,
    line_items: list[dict[str, Any]],
    currency: str = "IRR",
    tax_rate: float | Decimal = 0,
    number: str | None = None,
    customer_email: str | None = None,
    order_date: date | None = None,
    requested_delivery_date: date | None = None,
    notes: str | None = None,
    source_file_id: str | None = None,
    invoice_id: str | None = None,
) -> BusinessOrder:
    if not customer_name or not str(customer_name).strip():
        raise ValidationAppError("customer_name is required")
    if not line_items:
        raise ValidationAppError("At least one line item is required")

    rate = normalize_tax_rate(tax_rate)
    subtotal, tax_amount, total, normalized = _compute_totals(line_items, rate)

    source_uuid = None
    if source_file_id:
        try:
            source_uuid = uuid.UUID(str(source_file_id))
        except ValueError as exc:
            raise ValidationAppError("source_file_id must be a valid UUID") from exc
        await file_service.get_file(db, tenant_id=tenant_id, file_id=source_uuid)

    invoice_uuid = None
    if invoice_id:
        try:
            invoice_uuid = uuid.UUID(str(invoice_id))
        except ValueError as exc:
            raise ValidationAppError("invoice_id must be a valid UUID") from exc

    order = BusinessOrder(
        tenant_id=tenant_id,
        number=(number or _next_number_fallback()).strip()[:64],
        status="draft",
        currency=(currency or "IRR").upper()[:8],
        customer_name=str(customer_name).strip()[:255],
        customer_email=customer_email,
        order_date=order_date or date.today(),
        requested_delivery_date=requested_delivery_date,
        tax_rate=rate,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        line_items=normalized,
        notes=notes,
        source_file_id=source_uuid,
        invoice_id=invoice_uuid,
        created_by=actor_id,
        metadata_={},
    )
    db.add(order)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="order.created",
        resource_type="business_order",
        resource_id=str(order.id),
        metadata={"number": order.number, "total": float(order.total), "currency": order.currency},
    )
    return order


async def update_status(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    order_id: str,
    status: str,
) -> BusinessOrder:
    if status not in ALLOWED_STATUSES:
        raise ValidationAppError(f"status must be one of {sorted(ALLOWED_STATUSES)}")
    order = await get_order(db, tenant_id=tenant_id, order_id=order_id)
    order.status = status
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="order.status_updated",
        resource_type="business_order",
        resource_id=str(order.id),
        metadata={"status": status},
    )
    return order


async def get_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: str
) -> BusinessOrder:
    try:
        oid = uuid.UUID(str(order_id))
    except ValueError as exc:
        raise ValidationAppError("order_id must be a valid UUID") from exc
    result = await db.execute(
        select(BusinessOrder).where(
            BusinessOrder.id == oid,
            BusinessOrder.tenant_id == tenant_id,
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order not found")
    return order




async def find_order_for_customer(db: AsyncSession, *, tenant_id: uuid.UUID, order_id: str | None = None, order_number: str | None = None) -> BusinessOrder:
    stmt = select(BusinessOrder).where(BusinessOrder.tenant_id == tenant_id)
    if order_id:
        try:
            stmt = stmt.where(BusinessOrder.id == uuid.UUID(str(order_id)))
        except ValueError as exc:
            raise ValidationAppError("order_id must be a valid UUID") from exc
    elif order_number:
        stmt = stmt.where(BusinessOrder.number == str(order_number).strip())
    else:
        raise ValidationAppError("order_id or order_number is required")
    order = (await db.execute(stmt)).scalar_one_or_none()
    if order is None:
        raise NotFoundError("Order not found")
    return order

async def list_orders(
    db: AsyncSession, *, tenant_id: uuid.UUID, status: str | None = None
) -> list[BusinessOrder]:
    stmt = select(BusinessOrder).where(BusinessOrder.tenant_id == tenant_id)
    if status:
        if status not in ALLOWED_STATUSES:
            raise ValidationAppError(f"status must be one of {sorted(ALLOWED_STATUSES)}")
        stmt = stmt.where(BusinessOrder.status == status)
    stmt = stmt.order_by(BusinessOrder.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def order_summary(db: AsyncSession, *, tenant_id: uuid.UUID) -> dict[str, Any]:
    rows = await list_orders(db, tenant_id=tenant_id)
    counts: dict[str, int] = {}
    by_currency: dict[str, dict[str, float]] = {}
    for order in rows:
        counts[order.status] = counts.get(order.status, 0) + 1
        bucket = by_currency.setdefault(
            order.currency,
            {"open": 0.0, "delivered": 0.0, "cancelled": 0.0},
        )
        amount = float(order.total)
        if order.status == "delivered":
            bucket["delivered"] += amount
        elif order.status == "cancelled":
            bucket["cancelled"] += amount
        else:
            bucket["open"] += amount
    return {
        "currency_breakdown": by_currency,
        "counts_by_status": counts,
        "total_orders": len(rows),
    }


async def analyze_order_file(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    file_id: str,
) -> dict[str, Any]:
    try:
        source_uuid = uuid.UUID(str(file_id))
    except ValueError as exc:
        raise ValidationAppError("file_id must be a valid UUID") from exc

    source_file = await file_service.get_file(db, tenant_id=tenant_id, file_id=source_uuid)
    backend = storage.get_storage_backend()
    with backend.open(source_file.storage_key) as fh:
        raw = fh.read()

    text = ""
    name = (source_file.filename or "").lower()
    if name.endswith(".txt") or (source_file.content_type or "").startswith("text/"):
        text = raw.decode("utf-8", errors="replace")
    else:
        try:
            from app.services import document_service

            doc_result = await document_service.analyze_document(
                db, tenant_id=tenant_id, actor_id=actor_id, file_id=str(source_uuid)
            )
            text = doc_result.get("text_preview") or ""
            artifacts = doc_result.get("document_artifacts") or {}
            text_file_id = artifacts.get("extracted_text_file_id")
            if not text and text_file_id:
                tf = await file_service.get_file(
                    db, tenant_id=tenant_id, file_id=uuid.UUID(str(text_file_id))
                )
                with backend.open(tf.storage_key) as fh:
                    text = fh.read().decode("utf-8", errors="replace")
        except Exception:
            text = raw.decode("utf-8", errors="replace")

    amounts = _AMOUNT_RE.findall(text)[:20]
    dates = _DATE_RE.findall(text)[:20]
    emails = _EMAIL_RE.findall(text)[:10]
    numbers = [m.group(1) for m in _ORDER_NO_RE.finditer(text)][:10]

    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="order.analyzed",
        resource_type="file",
        resource_id=str(source_uuid),
        metadata={"amount_candidates": len(amounts), "date_candidates": len(dates)},
    )
    return {
        "file_id": str(source_uuid),
        "filename": source_file.filename,
        "order_number_candidates": numbers,
        "amount_candidates": amounts,
        "date_candidates": dates,
        "email_candidates": emails,
        "char_count": len(text),
        "excerpt": text[:2000],
    }


async def link_invoice(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    order_id: str,
    invoice_id: str,
) -> BusinessOrder:
    order = await get_order(db, tenant_id=tenant_id, order_id=order_id)
    try:
        inv_uuid = uuid.UUID(str(invoice_id))
    except ValueError as exc:
        raise ValidationAppError("invoice_id must be a valid UUID") from exc
    # Ensure invoice belongs to same tenant
    from app.models.business_invoice import BusinessInvoice

    result = await db.execute(
        select(BusinessInvoice).where(
            BusinessInvoice.id == inv_uuid,
            BusinessInvoice.tenant_id == tenant_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Invoice not found for this tenant")
    order.invoice_id = inv_uuid
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="order.linked_invoice",
        resource_type="business_order",
        resource_id=str(order.id),
        metadata={"invoice_id": str(inv_uuid)},
    )
    return order

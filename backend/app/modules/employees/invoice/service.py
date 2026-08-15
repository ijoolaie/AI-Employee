"""Invoice Employee domain service (Phase 7).

Persists tenant business invoices, analyzes incoming invoice files with the
same auditable regex approach as document_service, and exports PDF via
reportlab (shared toolchain with Report Employee — no second PDF stack).

Symbol name BusinessInvoice avoids any collision with Stripe billing.
"""

from __future__ import annotations

import io
import re
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.business_invoice import BusinessInvoice
from app.models.file import FileObject
from app.services import audit_service, file_service, storage

ALLOWED_STATUSES = frozenset({"draft", "sent", "paid", "overdue", "void"})

_AMOUNT_RE = re.compile(
    r"[\d,\.]{3,}\s?(?:ریال|تومان|﷼|\$|€|USD|IRR|EUR)\b|(?:\$|€)\s?[\d,\.]{2,}"
)
_DATE_RE = re.compile(
    r"\b(?:13|14)\d{2}[/\-]\d{1,2}[/\-]\d{1,2}\b|\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b|\b\d{1,2}[/\-]\d{1,2}[/\-]\d{4}\b"
)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_INVOICE_NO_RE = re.compile(
    r"(?:invoice|inv|فاکتور|شماره)\s*[:#]?\s*([A-Za-z0-9\-/]{3,32})",
    re.IGNORECASE,
)


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def normalize_tax_rate(raw: float | Decimal | int | str) -> Decimal:
    """Normalize model/API tax input to a percentage in [0, 100].

    LLMs often pass fractions (0.09 for 9%). Humans/API usually pass
    percent points (9 for 9%). Rule:
    - value in (0, 1]  → treat as fraction, convert to percent (* 100)
    - value in [0, 100] otherwise → treat as percent points
    Stored rate is always percent points so PDF/UI can show "Tax (9%)".
    """
    rate = Decimal(str(raw))
    if rate < 0:
        raise ValidationAppError("tax_rate must be >= 0")
    if Decimal("0") < rate <= Decimal("1"):
        rate = _money(rate * Decimal("100"))
    if rate > Decimal("100"):
        raise ValidationAppError("tax_rate must be <= 100 (percent points)")
    return rate



def _compute_totals(
    line_items: list[dict[str, Any]], tax_rate: Decimal
) -> tuple[Decimal, Decimal, Decimal, list[dict[str, Any]]]:
    normalized: list[dict[str, Any]] = []
    subtotal = Decimal("0")
    for raw in line_items:
        desc = str(raw.get("description") or "").strip()
        if not desc:
            raise ValidationAppError("Each line item needs a description")
        qty = Decimal(str(raw.get("quantity", 1)))
        unit = Decimal(str(raw.get("unit_price", 0)))
        if qty <= 0:
            raise ValidationAppError("Line item quantity must be > 0")
        if unit < 0:
            raise ValidationAppError("Line item unit_price must be >= 0")
        amount = _money(qty * unit)
        subtotal += amount
        normalized.append(
            {
                "description": desc[:500],
                "quantity": float(qty),
                "unit_price": float(unit),
                "amount": float(amount),
            }
        )
    subtotal = _money(subtotal)
    tax_amount = _money(subtotal * (tax_rate / Decimal("100")))
    total = _money(subtotal + tax_amount)
    return subtotal, tax_amount, total, normalized


def _next_number_fallback() -> str:
    return f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


async def create_invoice(
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
    issue_date: date | None = None,
    due_date: date | None = None,
    notes: str | None = None,
    source_file_id: str | None = None,
) -> BusinessInvoice:
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

    inv = BusinessInvoice(
        tenant_id=tenant_id,
        number=(number or _next_number_fallback()).strip()[:64],
        status="draft",
        currency=(currency or "IRR").upper()[:8],
        customer_name=str(customer_name).strip()[:255],
        customer_email=(customer_email or None),
        issue_date=issue_date or date.today(),
        due_date=due_date,
        tax_rate=rate,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        line_items=normalized,
        notes=notes,
        source_file_id=source_uuid,
        created_by=actor_id,
        metadata_={},
    )
    db.add(inv)
    await db.flush()

    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="invoice.created",
        resource_type="business_invoice",
        resource_id=str(inv.id),
        metadata={"number": inv.number, "total": float(inv.total), "currency": inv.currency},
    )
    return inv


async def update_status(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    invoice_id: str,
    status: str,
) -> BusinessInvoice:
    if status not in ALLOWED_STATUSES:
        raise ValidationAppError(f"status must be one of {sorted(ALLOWED_STATUSES)}")
    inv = await get_invoice(db, tenant_id=tenant_id, invoice_id=invoice_id)
    inv.status = status
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="invoice.status_updated",
        resource_type="business_invoice",
        resource_id=str(inv.id),
        metadata={"status": status},
    )
    return inv


async def get_invoice(
    db: AsyncSession, *, tenant_id: uuid.UUID, invoice_id: str
) -> BusinessInvoice:
    try:
        iid = uuid.UUID(str(invoice_id))
    except ValueError as exc:
        raise ValidationAppError("invoice_id must be a valid UUID") from exc
    result = await db.execute(
        select(BusinessInvoice).where(
            BusinessInvoice.id == iid,
            BusinessInvoice.tenant_id == tenant_id,
        )
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise NotFoundError("Invoice not found")
    return inv


async def list_invoices(
    db: AsyncSession, *, tenant_id: uuid.UUID, status: str | None = None
) -> list[BusinessInvoice]:
    stmt = select(BusinessInvoice).where(BusinessInvoice.tenant_id == tenant_id)
    if status:
        if status not in ALLOWED_STATUSES:
            raise ValidationAppError(f"status must be one of {sorted(ALLOWED_STATUSES)}")
        stmt = stmt.where(BusinessInvoice.status == status)
    stmt = stmt.order_by(BusinessInvoice.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def financial_summary(
    db: AsyncSession, *, tenant_id: uuid.UUID
) -> dict[str, Any]:
    rows = await list_invoices(db, tenant_id=tenant_id)
    counts: dict[str, int] = {}
    by_currency: dict[str, dict[str, float]] = {}
    for inv in rows:
        counts[inv.status] = counts.get(inv.status, 0) + 1
        bucket = by_currency.setdefault(
            inv.currency, {"outstanding": 0.0, "collected": 0.0, "voided": 0.0}
        )
        amount = float(inv.total)
        if inv.status == "paid":
            bucket["collected"] += amount
        elif inv.status == "void":
            bucket["voided"] += amount
        else:
            bucket["outstanding"] += amount
    return {
        "currency_breakdown": by_currency,
        "counts_by_status": counts,
        "total_invoices": len(rows),
    }


async def analyze_invoice_file(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    file_id: str,
) -> dict[str, Any]:
    """Extract invoice-like fields from an uploaded file (PDF/text/image path via document pipeline)."""
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
        # Reuse document_service text extraction when available
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
    numbers = [m.group(1) for m in _INVOICE_NO_RE.finditer(text)][:10]

    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="invoice.analyzed",
        resource_type="file",
        resource_id=str(source_uuid),
        metadata={"amount_candidates": len(amounts), "date_candidates": len(dates)},
    )
    return {
        "file_id": str(source_uuid),
        "filename": source_file.filename,
        "invoice_number_candidates": numbers,
        "amount_candidates": amounts,
        "date_candidates": dates,
        "email_candidates": emails,
        "char_count": len(text),
        "excerpt": text[:2000],
    }


def _render_invoice_pdf(inv: BusinessInvoice) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"Invoice {inv.number}")
    styles = getSampleStyleSheet()
    story: list[Any] = []
    story.append(Paragraph(f"Invoice {inv.number}", styles["Title"]))
    story.append(Paragraph(f"Status: {inv.status}", styles["Normal"]))
    story.append(Paragraph(f"Customer: {inv.customer_name}", styles["Normal"]))
    if inv.customer_email:
        story.append(Paragraph(f"Email: {inv.customer_email}", styles["Normal"]))
    story.append(
        Paragraph(
            f"Issue: {inv.issue_date} &nbsp;&nbsp; Due: {inv.due_date or '—'}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))

    data = [["Description", "Qty", "Unit", "Amount"]]
    for li in inv.line_items or []:
        data.append(
            [
                str(li.get("description", "")),
                str(li.get("quantity", "")),
                str(li.get("unit_price", "")),
                str(li.get("amount", "")),
            ]
        )
    data.append(["", "", "Subtotal", str(inv.subtotal)])
    data.append(["", "", f"Tax ({inv.tax_rate}%)", str(inv.tax_amount)])
    data.append(["", "", f"Total ({inv.currency})", str(inv.total)])

    table = Table(data, colWidths=[240, 60, 80, 80])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B4F72")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.append(table)
    if inv.notes:
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Notes: {inv.notes}", styles["Normal"]))
    doc.build(story)
    return buf.getvalue()


async def export_pdf(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    invoice_id: str,
) -> dict[str, Any]:
    inv = await get_invoice(db, tenant_id=tenant_id, invoice_id=invoice_id)
    pdf_bytes = _render_invoice_pdf(inv)
    if actor_id is None:
        raise ValidationAppError("export_pdf requires an authenticated actor")
    pdf_file = await file_service.upload_file(
        db,
        tenant_id=tenant_id,
        uploaded_by=actor_id,
        filename=f"{inv.number}_invoice.pdf",
        content_type="application/pdf",
        data=io.BytesIO(pdf_bytes),
    )
    inv.pdf_file_id = pdf_file.id
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="invoice.pdf_exported",
        resource_type="business_invoice",
        resource_id=str(inv.id),
        metadata={"pdf_file_id": str(pdf_file.id)},
    )
    return {
        "invoice_id": str(inv.id),
        "number": inv.number,
        "pdf_file_id": str(pdf_file.id),
        "total": float(inv.total),
        "currency": inv.currency,
        "status": inv.status,
    }

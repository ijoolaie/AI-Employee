"""Business invoice read/update API (Phase 7) — complements Invoice Employee tools."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.invoice import (
    BusinessInvoiceCreate,
    BusinessInvoiceResponse,
    BusinessInvoiceStatusUpdate,
    InvoiceFinancialSummary,
)
from app.services import invoice_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=APIResponse[list[BusinessInvoiceResponse]])
async def list_invoices(
    ctx: CurrentContext,
    db: DbSession,
    status: str | None = Query(default=None),
):
    rows = await invoice_service.list_invoices(db, tenant_id=ctx.tenant_id, status=status)
    return APIResponse(
        success=True,
        data=[BusinessInvoiceResponse.model_validate(r) for r in rows],
    )


@router.get("/summary", response_model=APIResponse[InvoiceFinancialSummary])
async def invoice_summary(ctx: CurrentContext, db: DbSession):
    data = await invoice_service.financial_summary(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=InvoiceFinancialSummary.model_validate(data))


@router.get("/{invoice_id}", response_model=APIResponse[BusinessInvoiceResponse])
async def get_invoice(invoice_id: UUID, ctx: CurrentContext, db: DbSession):
    inv = await invoice_service.get_invoice(
        db, tenant_id=ctx.tenant_id, invoice_id=str(invoice_id)
    )
    return APIResponse(success=True, data=BusinessInvoiceResponse.model_validate(inv))


@router.post(
    "",
    response_model=APIResponse[BusinessInvoiceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice(payload: BusinessInvoiceCreate, ctx: CurrentContext, db: DbSession):
    inv = await invoice_service.create_invoice(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        customer_name=payload.customer_name,
        line_items=[li.model_dump() for li in payload.line_items],
        currency=payload.currency,
        tax_rate=payload.tax_rate,
        number=payload.number,
        customer_email=payload.customer_email,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        notes=payload.notes,
        source_file_id=str(payload.source_file_id) if payload.source_file_id else None,
    )
    return APIResponse(success=True, data=BusinessInvoiceResponse.model_validate(inv))


@router.post("/{invoice_id}/status", response_model=APIResponse[BusinessInvoiceResponse])
async def update_status(
    invoice_id: UUID,
    payload: BusinessInvoiceStatusUpdate,
    ctx: CurrentContext,
    db: DbSession,
):
    inv = await invoice_service.update_status(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        invoice_id=str(invoice_id),
        status=payload.status,
    )
    # The async service may leave ORM attributes expired after audit/flush.
    # Refresh before Pydantic serialization to avoid implicit async IO.
    await db.refresh(inv)
    return APIResponse(success=True, data=BusinessInvoiceResponse.model_validate(inv))


@router.post("/{invoice_id}/export-pdf", response_model=APIResponse[dict])
async def export_pdf(invoice_id: UUID, ctx: CurrentContext, db: DbSession):
    result = await invoice_service.export_pdf(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        invoice_id=str(invoice_id),
    )
    return APIResponse(success=True, data=result)

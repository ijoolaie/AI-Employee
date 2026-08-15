"""Schemas for tenant business invoices (Phase 7)."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineItem(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(ge=0)
    amount: Decimal | None = None  # computed if omitted


class BusinessInvoiceCreate(BaseModel):
    number: str | None = Field(default=None, max_length=64)
    customer_name: str = Field(min_length=1, max_length=255)
    customer_email: str | None = None
    currency: str = Field(default="IRR", min_length=3, max_length=8)
    issue_date: date | None = None
    due_date: date | None = None
    tax_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        description="Percent points (9 = 9%). Values in (0,1] are normalized from fractions.",
    )
    line_items: list[InvoiceLineItem] = Field(min_length=1)
    notes: str | None = None
    source_file_id: UUID | None = None


class BusinessInvoiceStatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|sent|paid|overdue|void)$")


class BusinessInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    number: str
    status: str
    currency: str
    customer_name: str
    customer_email: str | None
    issue_date: date
    due_date: date | None
    tax_rate: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    line_items: list
    notes: str | None
    source_file_id: UUID | None
    pdf_file_id: UUID | None
    created_at: datetime
    updated_at: datetime


class InvoiceFinancialSummary(BaseModel):
    currency_breakdown: dict[str, dict[str, float]]
    counts_by_status: dict[str, int]
    total_invoices: int

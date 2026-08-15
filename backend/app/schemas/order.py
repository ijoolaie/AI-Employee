"""Schemas for tenant business orders (Phase 8)."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderLineItem(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(ge=0)
    amount: Decimal | None = None
    sku: str | None = Field(default=None, max_length=64)


class BusinessOrderCreate(BaseModel):
    number: str | None = Field(default=None, max_length=64)
    customer_name: str = Field(min_length=1, max_length=255)
    customer_email: str | None = None
    currency: str = Field(default="IRR", min_length=3, max_length=8)
    order_date: date | None = None
    requested_delivery_date: date | None = None
    tax_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        description="Percent points (9 = 9%). Values in (0,1] normalized from fractions.",
    )
    line_items: list[OrderLineItem] = Field(min_length=1)
    notes: str | None = None
    source_file_id: UUID | None = None
    invoice_id: UUID | None = None


class BusinessOrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(draft|confirmed|processing|shipped|delivered|cancelled)$"
    )


class BusinessOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    number: str
    status: str
    currency: str
    customer_name: str
    customer_email: str | None
    order_date: date
    requested_delivery_date: date | None
    tax_rate: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    line_items: list
    notes: str | None
    source_file_id: UUID | None
    invoice_id: UUID | None
    created_at: datetime
    updated_at: datetime


class OrderSummary(BaseModel):
    currency_breakdown: dict[str, dict[str, float]]
    counts_by_status: dict[str, int]
    total_orders: int

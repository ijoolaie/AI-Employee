from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class ProductCreate(BaseModel):
    sku: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=120)
    price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=8)
    inventory: int = Field(default=0, ge=0)
    attributes: dict[str, Any] = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list)

class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
    source: str
    created_at: datetime
    updated_at: datetime

class ProductInventoryUpdate(BaseModel):
    inventory: int = Field(ge=0)

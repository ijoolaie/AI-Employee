from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class CommerceIntegrationCreate(BaseModel):
    provider: str = Field(pattern="^(shopify|woocommerce|magento|custom_api|csv)$")
    name: str = Field(min_length=1, max_length=120)
    config: dict[str, Any] = Field(default_factory=dict)

class CommerceIntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    provider: str
    name: str
    status: str
    config: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

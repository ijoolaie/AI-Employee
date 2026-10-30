from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class CustomerChannelCreate(BaseModel):
    employee_id: UUID
    name: str = Field(min_length=1, max_length=120)
    channel_type: str = Field(default="web_widget", pattern="^(web_widget|public_chat|whatsapp)$")
    config: dict[str, Any] = Field(default_factory=dict)

class CustomerChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employee_id: UUID
    name: str
    channel_type: str
    public_key: str
    config: dict[str, Any]
    is_active: bool
    created_at: datetime

class PublicChannelResponse(BaseModel):
    public_key: str
    employee_id: UUID
    employee_name: str
    employee_slug: str
    channel_name: str
    channel_type: str
    config: dict[str, Any]

class PublicConversationCreate(BaseModel):
    customer_name: str | None = Field(default=None, max_length=160)
    customer_email: EmailStr | None = None
    customer_phone: str | None = Field(default=None, max_length=40)

class PublicMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)

class PublicMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

class PublicConversationResponse(BaseModel):
    id: UUID
    employee_name: str
    status: str
    customer_token: str | None = None
    email_verified: bool = False
    messages: list[PublicMessageResponse]

class CustomerConversationSummary(BaseModel):
    id: UUID
    employee_id: UUID
    channel_id: UUID
    status: str
    customer_name: str | None
    customer_email: str | None
    customer_phone: str | None
    message_count: int
    last_message: str | None
    updated_at: datetime


class PublicEmailVerificationCode(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

class PublicEmailVerificationResponse(BaseModel):
    verified: bool
    message: str


class PublicCustomerOrder(BaseModel):
    number: str
    status: str
    order_date: datetime | date
    total: Decimal
    currency: str

class PublicCustomerOrdersResponse(BaseModel):
    available: bool
    message: str
    source_fresh_at: datetime | None = None
    orders: list[PublicCustomerOrder] = Field(default_factory=list)

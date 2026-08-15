from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
class HandoffUpdate(BaseModel):
    requested: bool
    assigned_user_id: UUID | None = None
class InboxMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
class InboxMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
class InboxConversationResponse(BaseModel):
    id: UUID
    employee_id: UUID
    channel_id: UUID
    status: str
    handoff_requested: bool
    assigned_user_id: UUID | None
    customer_name: str | None
    customer_email: str | None
    customer_phone: str | None
    message_count: int
    last_message: str | None
    updated_at: datetime

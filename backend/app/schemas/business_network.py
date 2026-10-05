from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
class BusinessNetworkRequestCreate(BaseModel):
    recipient_tenant_id: UUID
    operation: str = Field(min_length=1,max_length=100)
    capability_contract: dict = Field(default_factory=dict)
    payload: dict = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1,max_length=200)
    correlation_id: str|None = Field(default=None,max_length=200)
    sponsor_user_id: UUID
class BusinessNetworkRequestDecision(BaseModel):
    approve: bool
    reason: str|None = Field(default=None,max_length=2000)
class BusinessNetworkRequestRead(BaseModel):
    id: UUID; sender_tenant_id: UUID; recipient_tenant_id: UUID; requester_user_id: UUID; sponsor_user_id: UUID
    operation: str; capability_contract: dict; payload: dict; idempotency_key: str; correlation_id: str; status: str
    decision_by: UUID|None; decision_reason: str|None; decided_at: datetime|None; created_at: datetime

"""Governed cross-company business-network request envelope."""
from __future__ import annotations
import enum, uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
class BusinessNetworkRequestStatus(str, enum.Enum):
    PENDING_APPROVAL="pending_approval"; APPROVED="approved"; REJECTED="rejected"; CANCELLED="cancelled"
class BusinessNetworkRequest(Base):
    __tablename__="business_network_requests"
    __table_args__=(UniqueConstraint("sender_tenant_id","idempotency_key",name="uq_business_network_sender_idempotency"),Index("ix_business_network_requests_sender_status","sender_tenant_id","status"),Index("ix_business_network_requests_recipient_status","recipient_tenant_id","status"))
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    sender_tenant_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("tenants.id",ondelete="RESTRICT"),nullable=False)
    recipient_tenant_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("tenants.id",ondelete="RESTRICT"),nullable=False)
    requester_user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="RESTRICT"),nullable=False)
    sponsor_user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="RESTRICT"),nullable=False)
    operation: Mapped[str]=mapped_column(String(100),nullable=False)
    capability_contract: Mapped[dict]=mapped_column(JSONB,nullable=False,default=dict)
    payload: Mapped[dict]=mapped_column(JSONB,nullable=False,default=dict)
    idempotency_key: Mapped[str]=mapped_column(String(200),nullable=False)
    correlation_id: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    status: Mapped[BusinessNetworkRequestStatus]=mapped_column(Enum(BusinessNetworkRequestStatus,values_callable=lambda e:[x.value for x in e]),nullable=False,default=BusinessNetworkRequestStatus.PENDING_APPROVAL)
    decision_by: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="RESTRICT"),nullable=True)
    decision_reason: Mapped[str|None]=mapped_column(Text,nullable=True)
    decided_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)

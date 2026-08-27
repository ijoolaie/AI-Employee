"""Canonical WorkItem domain model for the Human + Agent execution layer."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkItemStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    ASSIGNED = "assigned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class ExecutorType(str, enum.Enum):
    HUMAN = "human"
    AGENT = "agent"


class WorkItem(Base):
    __tablename__ = "work_items"
    __table_args__ = (
        Index("ix_work_items_tenant_status", "tenant_id", "status"),
        Index("ix_work_items_tenant_executor", "tenant_id", "executor_type", "executor_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[WorkItemStatus] = mapped_column(Enum(WorkItemStatus), nullable=False, default=WorkItemStatus.DRAFT)
    priority: Mapped[int] = mapped_column(nullable=False, default=0)
    requester_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    executor_type: Mapped[ExecutorType | None] = mapped_column(Enum(ExecutorType))
    executor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSONB)
    policy_context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_work_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

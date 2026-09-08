"""Durable, tenant-scoped Agent-to-Agent delegation authority."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentDelegation(Base):
    __tablename__ = "agent_delegations"
    __table_args__ = (
        Index("ix_agent_delegations_tenant_status", "tenant_id", "status"),
        Index("ix_agent_delegations_target", "tenant_id", "delegate_agent_instance_id"),
        Index("ix_agent_delegations_source", "tenant_id", "delegator_agent_instance_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    delegator_agent_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_instances.id"), nullable=False)
    delegate_agent_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_instances.id"), nullable=False)
    source_work_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False)
    delegated_work_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True)
    scopes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    chain_depth: Mapped[int] = mapped_column(nullable=False, default=1)
    max_chain_depth: Mapped[int] = mapped_column(nullable=False, default=3)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

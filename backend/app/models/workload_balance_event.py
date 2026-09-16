"""Durable recommendation evidence for Stage 9 workload balancing."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkloadBalanceEvent(Base):
    """Immutable snapshot of a queue-aware balancing recommendation."""

    __tablename__ = "workload_balance_events"
    __table_args__ = (
        Index("ix_workload_balance_events_tenant_created", "tenant_id", "created_at"),
        Index("ix_workload_balance_events_tenant_target", "tenant_id", "target_agent_instance_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    target_agent_instance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_instances.id", ondelete="RESTRICT"), nullable=True
    )
    ready_items: Mapped[int] = mapped_column(Integer, nullable=False)
    oldest_ready_age_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    total_available_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    queue_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    candidates_considered: Mapped[int] = mapped_column(Integer, nullable=False)
    rationale: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    contract_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

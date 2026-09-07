"""Immutable evaluation evidence for governed AgentTemplates."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentEvaluationStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentEvaluation(Base):
    __tablename__ = "agent_evaluations"
    __table_args__ = (
        Index("ix_agent_evaluations_template_created", "agent_template_id", "created_at"),
        Index("ix_agent_evaluations_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    agent_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_templates.id", ondelete="RESTRICT"), nullable=False)
    suite_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[AgentEvaluationStatus] = mapped_column(
        Enum(AgentEvaluationStatus, values_callable=lambda cls: [item.value for item in cls], name="agentevaluationstatus"),
        nullable=False,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    evaluator_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

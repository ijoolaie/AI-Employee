"""Governed proposal lifecycle for dynamic Agent workforce capacity."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentWorkforceProposalStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    BOARD_APPROVED = "board_approved"
    BOARD_REJECTED = "board_rejected"
    CEO_APPROVED = "ceo_approved"
    CEO_REJECTED = "ceo_rejected"
    PROVISIONED = "provisioned"
    CANCELLED = "cancelled"


class AgentWorkforceProposal(Base):
    __tablename__ = "agent_workforce_proposals"
    __table_args__ = (
        Index("ix_agent_workforce_proposals_tenant_status", "tenant_id", "status"),
        Index("ix_agent_workforce_proposals_tenant_template", "tenant_id", "agent_template_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    agent_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_templates.id", ondelete="RESTRICT"), nullable=True)
    agent_definition_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_definitions.id", ondelete="RESTRICT"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    requested_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sponsor_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    risk_tier: Mapped[int] = mapped_column(nullable=False, default=0)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[AgentWorkforceProposalStatus] = mapped_column(
        Enum(AgentWorkforceProposalStatus, values_callable=lambda enum_type: [item.value for item in enum_type]),
        nullable=False,
        default=AgentWorkforceProposalStatus.SUBMITTED,
    )
    board_reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    board_decision_reason: Mapped[str | None] = mapped_column(Text)
    ceo_approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ceo_decision_reason: Mapped[str | None] = mapped_column(Text)
    provisioned_agent_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_instances.id", ondelete="RESTRICT"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

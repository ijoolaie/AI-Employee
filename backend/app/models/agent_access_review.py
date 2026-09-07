"""Periodic, explicit access review records for AgentIdentity."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentAccessReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    REVOKED = "revoked"


class AgentAccessReview(Base):
    __tablename__ = "agent_access_reviews"
    __table_args__ = (
        Index("ix_agent_access_reviews_tenant_identity", "tenant_id", "agent_identity_id"),
        Index("ix_agent_access_reviews_due", "tenant_id", "next_review_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    agent_identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_identities.id", ondelete="CASCADE"), nullable=False)
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision: Mapped[AgentAccessReviewDecision] = mapped_column(
        Enum(AgentAccessReviewDecision, values_callable=lambda cls: [item.value for item in cls], name="agentaccessreviewdecision"),
        nullable=False,
    )
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

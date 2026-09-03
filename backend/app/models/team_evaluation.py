"""Immutable evaluation evidence for versioned Agent Teams."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, event, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TeamEvaluation(Base):
    """Point-in-time evaluation record tied to an immutable TeamVersion."""

    __tablename__ = "team_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    team_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("team_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    evaluator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    evaluation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    score: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="recorded")
    evidence_class: Mapped[str] = mapped_column(String(32), nullable=False, default="engineering")
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


@event.listens_for(TeamEvaluation, "before_update")
def _reject_evaluation_update(mapper, connection, target) -> None:
    raise ValueError("team evaluation records are immutable")

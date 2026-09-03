"""Versioned, tenant-owned Agent Team contract."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.team_definition import TeamDefinition


class TeamVersion(Base):
    """A published team contract; historical versions are never updated by design."""

    __tablename__ = "team_versions"
    __table_args__ = (
        UniqueConstraint("team_id", "version", name="uq_team_versions_team_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("team_definitions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    member_agent_definition_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    roles: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    execution_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    allowed_tools: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    input_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team: Mapped["TeamDefinition"] = relationship(back_populates="versions")

"""Test Center definition contract (P12.1)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TestDefinition(Base):
    __tablename__ = "test_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_test_definitions_tenant_code"),
        Index("ix_test_definitions_tenant_workspace", "tenant_id", "workspace_key"),
        Index("ix_test_definitions_tenant_enabled", "tenant_id", "enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_type: Mapped[str] = mapped_column(String(50), nullable=False, default="acceptance")
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="backend")
    description: Mapped[str | None] = mapped_column(Text)
    workspace_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prerequisites: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    expected_result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_requirements: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

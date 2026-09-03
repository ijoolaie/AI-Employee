"""Test Center run lifecycle and evidence identity persistence (P12.3/P12.4)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TestRunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TestRun(Base):
    __tablename__ = "test_runs"
    __table_args__ = (
        Index("ix_test_runs_tenant_created", "tenant_id", "created_at"),
        Index("ix_test_runs_tenant_status", "tenant_id", "status"),
        Index("ix_test_runs_tenant_definition", "tenant_id", "test_definition_id"),
        Index("ix_test_runs_tenant_workspace", "tenant_id", "workspace_key"),
        Index("ix_test_runs_tenant_git_sha", "tenant_id", "git_sha"),
        Index("ix_test_runs_status_queued_started", "status", "queued_at", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    test_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_definitions.id", ondelete="RESTRICT"), nullable=False
    )
    workspace_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[TestRunStatus] = mapped_column(
        Enum(TestRunStatus, values_callable=lambda enum_type: [item.value for item in enum_type]),
        nullable=False,
        default=TestRunStatus.QUEUED,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    executor_type: Mapped[str] = mapped_column(String(30), nullable=False, default="backend")
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    fixtures: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_version: Mapped[str | None] = mapped_column(String(120))
    migration_identity: Mapped[str | None] = mapped_column(String(120))
    git_sha: Mapped[str | None] = mapped_column(String(64))
    evidence_boundary: Mapped[str] = mapped_column(
        String(80), nullable=False, default="engineering_product_evidence"
    )
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

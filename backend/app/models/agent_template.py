"""Reusable, governed, installable packaging of an AgentDefinition."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentTemplateStatus(str, enum.Enum):
    DRAFT = "draft"
    EVALUATING = "evaluating"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class AgentTemplate(Base):
    __tablename__ = "agent_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", "version", name="uq_agent_templates_tenant_slug_version"),
        Index("ix_agent_templates_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    agent_definition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_definitions.id"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, insert_default=1)
    status: Mapped[AgentTemplateStatus] = mapped_column(
        Enum(AgentTemplateStatus, values_callable=lambda cls: [item.value for item in cls], name="agenttemplatestatus"),
        nullable=False,
        default=AgentTemplateStatus.DRAFT,
        insert_default=AgentTemplateStatus.DRAFT,
    )
    risk_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=0, insert_default=0)
    capability_contract: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    permission_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    approval_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    evaluation_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    install_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_system_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, insert_default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

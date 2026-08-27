"""Tenant-scoped deployment of an AgentDefinition."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentInstanceStatus(str, enum.Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    DRAINING = "draining"


class AgentInstance(Base):
    __tablename__ = "agent_instances"
    __table_args__ = (Index("ix_agent_instances_tenant_definition", "tenant_id", "agent_definition_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    agent_definition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_definitions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[AgentInstanceStatus] = mapped_column(Enum(AgentInstanceStatus), nullable=False, default=AgentInstanceStatus.ENABLED)
    max_concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    budget_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

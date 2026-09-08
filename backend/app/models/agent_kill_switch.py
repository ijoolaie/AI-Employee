"""Durable emergency execution revocation state for governed Agents."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentKillScope(str, enum.Enum):
    GLOBAL = "global"
    TENANT = "tenant"
    AGENT = "agent"


class AgentKillSwitch(Base):
    __tablename__ = "agent_kill_switches"
    __table_args__ = (
        Index("ix_agent_kill_switches_active_tenant", "tenant_id", "active"),
        Index("ix_agent_kill_switches_active_agent", "agent_instance_id", "active"),
        Index("ix_agent_kill_switches_active_scope", "scope", "active"),
        Index(
            "uq_agent_kill_switch_global_active",
            "scope",
            unique=True,
            postgresql_where=text("scope = 'global' AND active = true"),
        ),
        Index(
            "uq_agent_kill_switch_tenant_active",
            "scope",
            "tenant_id",
            unique=True,
            postgresql_where=text("scope = 'tenant' AND active = true"),
        ),
        Index(
            "uq_agent_kill_switch_agent_active",
            "scope",
            "tenant_id",
            "agent_instance_id",
            unique=True,
            postgresql_where=text("scope = 'agent' AND active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True
    )
    agent_instance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_instances.id", ondelete="CASCADE"), nullable=True
    )
    scope: Mapped[AgentKillScope] = mapped_column(
        Enum(
            AgentKillScope,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="agentkillscope",
        ),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    asserted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    asserted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)

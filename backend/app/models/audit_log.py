"""Audit Log model — sراسری (global) record of sensitive actions.

Per docs v1.2 (21_CrossCutting_Additions §3.4): independent Core module,
not a side-effect of another table. Written to on every sensitive
operation (auth events, role/permission changes, tenant settings changes,
Employee Run creation, AI Provider calls) via app.services.audit_service.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # NULL tenant_id = platform-level action (e.g. superuser action outside a tenant)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True
    )

    # Who performed the action. actor_type distinguishes human vs system/service actors.
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "user" | "system" | "worker"
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # What happened. Free-form but conventionally "<resource>.<verb>",
    # e.g. "auth.login", "role.assigned", "employee.run_created", "ai.provider_call".
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Correlates to the request/trace that produced this entry (see app.core.logging).
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Outcome + free-form context. Never store secrets/PII payloads here —
    # only enough to reconstruct "what happened", per 14_Security data-minimization.
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    # "success" | "failure" | "denied"
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

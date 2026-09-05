"""Run — one execution of an Employee (11_Employee_Framework §5).

Status machine: pending -> running -> success | failed | cancelled | waiting
("waiting" = paused for Human Approval, per 10_AI_Core §3.8/§2 and
12_Workflow_Engine §7). Locked to employee_version_id so the definition
used cannot silently change out from under a historical Run — required
for Replay (04_Architecture goal #4).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    employee_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employee_versions.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_conversations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    # pending | running | success | failed | cancelled | waiting

    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Aggregate cost/usage across all AI Provider calls in this Run — rolled
    # up from ai_provider_calls (see app.models.ai_provider_call), read by
    # the Cost Dashboard (docs v1.2 §3.5, Phase 2).
    total_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)

    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    @property
    def error_message(self) -> str | None:
        """Compatibility view over the persisted structured execution error."""
        if isinstance(self.error, dict):
            message = self.error.get("message")
            return str(message) if message is not None else None
        return None

    @error_message.setter
    def error_message(self, value: str | None) -> None:
        """Persist legacy error-message assignments in the structured field."""
        self.error = None if value is None else {
            "code": "RUN_EXECUTION_FAILED",
            "message": str(value)[:2000],
        }

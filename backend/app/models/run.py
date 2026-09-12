"""Run — one execution of an Employee or governed Agent instance."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    employee_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employee_versions.id"), nullable=False)
    agent_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_instances.id", ondelete="RESTRICT"), nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customer_conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_step_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_step_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_parallel_branch_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_parallel_branch_runs.id", ondelete="SET NULL"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    __table_args__ = (
        UniqueConstraint("workflow_step_run_id", name="uq_runs_workflow_step_run_id"),
        UniqueConstraint("workflow_parallel_branch_run_id", name="uq_runs_workflow_parallel_branch_run_id"),
    )

    @property
    def prompt_tokens(self) -> int:
        return int(getattr(self, "_prompt_tokens", 0))

    @prompt_tokens.setter
    def prompt_tokens(self, value: int) -> None:
        self._prompt_tokens = int(value)
        self.total_tokens = self.prompt_tokens + self.completion_tokens

    @property
    def completion_tokens(self) -> int:
        return int(getattr(self, "_completion_tokens", 0))

    @completion_tokens.setter
    def completion_tokens(self, value: int) -> None:
        self._completion_tokens = int(value)
        self.total_tokens = self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self) -> float:
        return float(self.total_cost_usd or 0)

    @cost_usd.setter
    def cost_usd(self, value: float) -> None:
        self.total_cost_usd = value

    @property
    def error_message(self) -> str | None:
        if isinstance(self.error, dict):
            message = self.error.get("message")
            return str(message) if message is not None else None
        return None

    @error_message.setter
    def error_message(self, value: str | None) -> None:
        self.error = None if value is None else {"code": "RUN_EXECUTION_FAILED", "message": str(value)[:2000]}

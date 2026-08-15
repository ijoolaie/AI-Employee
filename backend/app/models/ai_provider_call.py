"""AI Gateway call log.

Per 10_AI_Core §3.1: the Gateway "ثبت latency، tokens و cost برای هر
فراخوانی" (records latency, tokens, cost for every call). This table is
that record. It is the data source for:
  - Trace / Replay of a Run (each row links to run_id)
  - The Cost Dashboard (docs v1.2 §3.5, Phase 2) — a UI is added later,
    but the underlying rows must exist from the first real AI call.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIProviderCall(Base):
    __tablename__ = "ai_provider_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True, index=True
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    # "success" | "error" | "timeout"
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Prompt version used, for Prompt Versioning traceability (10_AI_Core §3.3)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    raw_meta: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

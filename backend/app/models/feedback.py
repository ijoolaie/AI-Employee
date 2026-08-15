"""Feedback — Phase 3 "Validation" support (03_Roadmap_v1.1 §6).

Per the Roadmap, Phase 3 is a customer-validation phase, not an engineering
phase: its Definition of Done is "حداقل ۳ مشتری فعال که به‌طور منظم از
Report Employee استفاده می‌کنند و بازخورد کیفی ثبت شده است" (at least 3
active customers regularly using the Report Employee, with qualitative
feedback recorded). This model exists purely to let that feedback actually
be *recorded* in the product instead of living in email/spreadsheets —
it does not, and cannot, constitute Phase 3 completion by itself. See
documents/59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # Optional link to the Run the feedback is about (e.g. "this report was
    # useful/not useful"). Nullable so general product feedback is also
    # supported, not only per-Run feedback.
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True, index=True
    )
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True
    )

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "run" | "general" — lets the Validation dashboard separate per-report
    # reactions from broader product feedback without a schema change.
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="run")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

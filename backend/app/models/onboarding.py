import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    business_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    setup_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

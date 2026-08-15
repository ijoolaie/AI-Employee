"""Transactional outbox records used for durable post-commit dispatch."""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class OutboxMessage(Base):
    __tablename__ = "outbox_messages"

    def __init__(self, **kwargs):
        # SQLAlchemy's mapped_column(default=...) values are applied at INSERT
        # time, not when constructing the Python object. Keep the in-memory
        # object aligned with the durable defaults expected by the outbox
        # contract and tests.
        kwargs.setdefault("status", "pending")
        kwargs.setdefault("attempts", 0)
        super().__init__(**kwargs)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    dead_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

Index("ix_outbox_pending_available", OutboxMessage.status, OutboxMessage.available_at)
Index("uq_outbox_dedupe_key", OutboxMessage.dedupe_key, unique=True, postgresql_where=OutboxMessage.dedupe_key.is_not(None))
Index("ix_outbox_dead_at", OutboxMessage.dead_at)

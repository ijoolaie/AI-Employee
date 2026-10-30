from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CustomerConversationSlot(Base):
    """A validated customer-provided support fact with message provenance."""

    __tablename__ = "customer_conversation_slots"
    __table_args__ = (
        CheckConstraint(
            "slot_name IN ('city', 'order_id', 'payment_reference', 'product', 'color', 'size', 'quantity', 'reason', 'issue_details')",
            name="ck_customer_conversation_slots_name",
        ),
        CheckConstraint(
            "(slot_name = 'quantity' AND jsonb_typeof(value) = 'number') OR "
            "(slot_name <> 'quantity' AND jsonb_typeof(value) = 'string')",
            name="ck_customer_conversation_slots_value_type",
        ),
        UniqueConstraint(
            "tenant_id", "conversation_id", "slot_name",
            name="uq_customer_conversation_slots_current",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "conversation_id"],
            ["customer_conversations.tenant_id", "customer_conversations.id"],
            ondelete="CASCADE",
            name="fk_customer_conversation_slots_conversation_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "conversation_id", "source_message_id"],
            [
                "customer_messages.tenant_id",
                "customer_messages.conversation_id",
                "customer_messages.id",
            ],
            ondelete="CASCADE",
            name="fk_customer_conversation_slots_source_message",
        ),
        Index(
            "ix_customer_conversation_slots_expiry",
            "tenant_id", "conversation_id", "expires_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    slot_name: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

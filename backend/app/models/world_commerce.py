"""World Mode catalogue, one-time orders, and append-only commerce events.

These records are separate from SaaS subscriptions. Prices and provider options
are server-owned catalogue data; order rows snapshot the agreed amount/currency.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorldCatalogueItem(Base):
    __tablename__ = "world_catalogue_items"
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('room', 'layout', 'appearance', 'personality', 'furniture', 'facility', 'support')",
            name="ck_world_catalogue_item_type",
        ),
        Index("ix_world_catalogue_active_type", "is_active", "item_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    item_type: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Server-managed options, e.g. IRR/USD/USDT price amounts and allowed providers.
    # Never accept these values from a client request.
    price_options: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_free: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WorldOrder(Base):
    __tablename__ = "world_orders"
    __table_args__ = (
        CheckConstraint("currency IN ('IRR', 'USD', 'USDT', 'WORLD_CREDIT')", name="ck_world_order_currency"),
        CheckConstraint(
            "status IN ('pending_payment', 'payment_submitted', 'approved', 'rejected', 'fulfilled', 'cancelled')",
            name="ck_world_order_status",
        ),
        CheckConstraint("amount >= 0", name="ck_world_order_amount_nonnegative"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_world_order_tenant_idempotency"),
        Index("ix_world_orders_tenant_status_created", "tenant_id", "status", "created_at"),
        Index("ix_world_orders_status_created", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    buyer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    catalogue_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("world_catalogue_items.id", ondelete="RESTRICT"), nullable=False)
    item_code_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_transaction_ref: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_payment")
    payment_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    approved_by_username: Mapped[str | None] = mapped_column(String(320))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    activated_by_username: Mapped[str | None] = mapped_column(String(320))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WorldCommerceEvent(Base):
    """Append-only timeline of order, payment approval, and feature activation."""

    __tablename__ = "world_commerce_events"
    __table_args__ = (
        Index("ix_world_commerce_events_tenant_created", "tenant_id", "created_at"),
        Index("ix_world_commerce_events_order_created", "order_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("world_orders.id", ondelete="RESTRICT"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    actor_username: Mapped[str | None] = mapped_column(String(320))
    from_status: Mapped[str | None] = mapped_column(String(24))
    to_status: Mapped[str | None] = mapped_column(String(24))
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

"""File metadata model.

The binary itself lives in Object Storage (local disk in dev, S3-compatible
in production — see app.services.storage). This table only tracks
metadata + tenant ownership, per 07_Backend §5.5 and the Tenant isolation
rules in 14_Security §5 (storage paths are namespaced by tenant_id).
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FileObject(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Storage-backend-relative path, always prefixed with tenant_id — never
    # trust a client-supplied path. See app.services.storage.build_key().
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # "active" | "deleted" (soft delete, per 14_Security §6)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

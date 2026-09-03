"""File upload/list/delete — always tenant-scoped (see core.deps.TenantContext)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import request_id_var
from app.models.file import FileObject
from app.services import audit_service, storage
from app.services.file_policy import max_file_size, max_files_per_tenant, tenant_storage_quota, validate_content_type


class _LimitedReader:
    """Bound a file-like object so storage never receives more than a quota window."""

    def __init__(self, source, limit: int):
        self.source = source
        self.remaining = max(0, limit)

    def read(self, size: int = -1):
        if self.remaining <= 0:
            return b""
        if size is None or size < 0:
            size = self.remaining
        chunk = self.source.read(min(size, self.remaining))
        self.remaining -= len(chunk)
        return chunk


async def upload_file(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    filename: str,
    content_type: str | None,
    data,
) -> FileObject:
    filename = filename.strip() or "unnamed"
    try:
        validate_content_type(content_type, filename)
    except ValueError as exc:
        raise ValidationAppError(str(exc)) from exc

    max_size = max_file_size()
    quota = tenant_storage_quota()
    file_count_limit = max_files_per_tenant()

    active_count = int(
        (await db.execute(
            select(func.count(FileObject.id)).where(
                FileObject.tenant_id == tenant_id,
                FileObject.status == "active",
            )
        )).scalar_one()
        or 0
    )
    if active_count >= file_count_limit:
        raise ValidationAppError(
            "Tenant file count quota exceeded",
            details={"max_files": file_count_limit},
        )

    used_bytes = int(
        (await db.execute(
            select(func.coalesce(func.sum(FileObject.size_bytes), 0)).where(
                FileObject.tenant_id == tenant_id,
                FileObject.status == "active",
            )
        )).scalar_one()
        or 0
    )
    remaining_quota = quota - used_bytes
    if remaining_quota <= 0:
        raise ValidationAppError(
            "Tenant storage quota exceeded",
            details={"quota_bytes": quota, "used_bytes": used_bytes},
        )

    write_limit = min(max_size, remaining_quota) + 1
    key = storage.build_key(str(tenant_id), filename)
    backend = storage.get_storage_backend()
    size = backend.save(key, _LimitedReader(data, write_limit))

    if size > max_size:
        backend.delete(key)
        raise ValidationAppError(
            "File exceeds maximum allowed size",
            details={"max_file_size_bytes": max_size},
        )
    if size > remaining_quota:
        backend.delete(key)
        raise ValidationAppError(
            "Tenant storage quota exceeded",
            details={"quota_bytes": quota, "used_bytes": used_bytes},
        )

    file_obj = FileObject(
        tenant_id=tenant_id,
        uploaded_by=uploaded_by,
        filename=filename,
        content_type=content_type,
        size_bytes=size,
        storage_key=key,
        status="active",
    )
    db.add(file_obj)
    await db.flush()
    await db.refresh(file_obj)

    await audit_service.record(
        db,
        action="file.uploaded",
        actor_type="user",
        actor_id=uploaded_by,
        tenant_id=tenant_id,
        resource_type="file",
        resource_id=file_obj.id,
        request_id=request_id_var.get(),
        metadata={"filename": filename, "size_bytes": size, "tenant_storage_used_bytes": used_bytes + size},
    )
    return file_obj


async def list_files(db: AsyncSession, *, tenant_id: uuid.UUID) -> list[FileObject]:
    result = await db.execute(
        select(FileObject)
        .where(FileObject.tenant_id == tenant_id, FileObject.status == "active")
        .order_by(FileObject.created_at.desc())
    )
    return list(result.scalars().all())


async def get_file(db: AsyncSession, *, tenant_id: uuid.UUID, file_id: uuid.UUID) -> FileObject:
    result = await db.execute(
        select(FileObject).where(
            FileObject.id == file_id,
            FileObject.tenant_id == tenant_id,
            FileObject.status == "active",
        )
    )
    file_obj = result.scalar_one_or_none()
    if file_obj is None:
        raise NotFoundError("File not found")
    return file_obj


async def soft_delete_file(
    db: AsyncSession, *, tenant_id: uuid.UUID, file_id: uuid.UUID, actor_id: uuid.UUID
) -> None:
    file_obj = await get_file(db, tenant_id=tenant_id, file_id=file_id)
    file_obj.status = "deleted"
    file_obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()

    await audit_service.record(
        db,
        action="file.deleted",
        actor_type="user",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_type="file",
        resource_id=file_obj.id,
        request_id=request_id_var.get(),
    )

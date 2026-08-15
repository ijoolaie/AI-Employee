"""File upload/list/delete — always tenant-scoped (see core.deps.TenantContext)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import request_id_var
from app.models.file import FileObject
from app.services import audit_service, storage


async def upload_file(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    filename: str,
    content_type: str | None,
    data,
) -> FileObject:
    key = storage.build_key(str(tenant_id), filename)
    backend = storage.get_storage_backend()
    size = backend.save(key, data)

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
        metadata={"filename": filename, "size_bytes": size},
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

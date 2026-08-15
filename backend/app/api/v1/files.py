"""File endpoints: upload, list, download, delete. Always scoped to the caller's tenant."""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.deps import DbSession, FileReadContext, FileWriteContext
from app.schemas.common import APIResponse
from app.schemas.file import FileResponse
from app.services import file_service, storage

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=APIResponse[FileResponse], status_code=status.HTTP_201_CREATED)
async def upload(ctx: FileWriteContext, db: DbSession, file: UploadFile = File(...)):
    file_obj = await file_service.upload_file(
        db,
        tenant_id=ctx.tenant_id,
        uploaded_by=ctx.user_id,
        filename=file.filename or "unnamed",
        content_type=file.content_type,
        data=file.file,
    )
    return APIResponse(success=True, data=FileResponse.model_validate(file_obj))


@router.get("", response_model=APIResponse[list[FileResponse]])
async def list_files(ctx: FileReadContext, db: DbSession):
    files = await file_service.list_files(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=[FileResponse.model_validate(f) for f in files])


@router.get("/{file_id}", response_model=APIResponse[FileResponse])
async def get_file(file_id: UUID, ctx: FileReadContext, db: DbSession):
    file_obj = await file_service.get_file(db, tenant_id=ctx.tenant_id, file_id=file_id)
    return APIResponse(success=True, data=FileResponse.model_validate(file_obj))


@router.get("/{file_id}/download")
async def download_file(file_id: UUID, ctx: FileReadContext, db: DbSession):
    """Stream the file's bytes. Added in Phase 2 so generated report artifacts
    (PDF/Excel/chart PNGs from the Report Employee) — and any previously
    uploaded file — are actually retrievable, not just listed as metadata.
    Tenant-scoped through file_service.get_file exactly like the other
    /files routes; the storage key is never trusted from client input."""
    file_obj = await file_service.get_file(db, tenant_id=ctx.tenant_id, file_id=file_id)
    backend = storage.get_storage_backend()
    stream = backend.open(file_obj.storage_key)
    return StreamingResponse(
        stream,
        media_type=file_obj.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_obj.filename}"'},
    )


@router.delete("/{file_id}", response_model=APIResponse[None])
async def delete_file(file_id: UUID, ctx: FileWriteContext, db: DbSession):
    await file_service.soft_delete_file(
        db, tenant_id=ctx.tenant_id, file_id=file_id, actor_id=ctx.user_id
    )
    return APIResponse(success=True, data=None)

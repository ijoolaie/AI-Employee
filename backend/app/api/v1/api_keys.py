from uuid import UUID
from fastapi import APIRouter, status
from app.core.deps import CurrentContext, DbSession
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyResponse
from app.schemas.common import APIResponse
from app.services import api_key_service, audit_service
from app.core.logging import request_id_var

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _response(row: APIKey) -> APIKeyResponse:
    return APIKeyResponse.model_validate(row)


@router.get("", response_model=APIResponse[list[APIKeyResponse]])
async def list_api_keys(ctx: CurrentContext, db: DbSession):
    rows = await api_key_service.list_keys(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=[_response(r) for r in rows])


@router.post("", response_model=APIResponse[APIKeyCreated], status_code=status.HTTP_201_CREATED)
async def create_api_key(payload: APIKeyCreate, ctx: CurrentContext, db: DbSession):
    row, secret = await api_key_service.create_key(
        db, tenant_id=ctx.tenant_id, user_id=ctx.user_id,
        name=payload.name.strip(), expires_at=payload.expires_at
    )
    await audit_service.record(
        db, action="api_key.created", actor_type="user", actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id, resource_type="api_key", resource_id=row.id,
        request_id=request_id_var.get(), metadata={"name": row.name, "key_prefix": row.key_prefix}
    )
    return APIResponse(success=True, data=APIKeyCreated(**_response(row).model_dump(), key=secret))


@router.post("/{key_id}/revoke", response_model=APIResponse[APIKeyResponse])
async def revoke_api_key(key_id: UUID, ctx: CurrentContext, db: DbSession):
    row = await api_key_service.revoke_key(db, tenant_id=ctx.tenant_id, key_id=key_id)
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="API key not found")
    await audit_service.record(
        db, action="api_key.revoked", actor_type="user", actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id, resource_type="api_key", resource_id=row.id,
        request_id=request_id_var.get(), metadata={"key_prefix": row.key_prefix}
    )
    return APIResponse(success=True, data=_response(row))

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.core.deps import APIKeysCreateContext, APIKeysReadContext, APIKeysRevokeContext, DbSession, TenantContext
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyResponse
from app.schemas.common import APIResponse
from app.services import api_key_service, audit_service
from app.core.logging import request_id_var
from app.core.edition_deps import EDITION_SCOPE_ALLOWLIST_BY_KIND
from app.models.role import Permission

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _response(row: APIKey) -> APIKeyResponse:
    return APIKeyResponse.model_validate(row)


def _owner_permissions(ctx: TenantContext) -> set[str]:
    return {
        permission.code
        for role in ctx.user.roles
        if role.tenant_id == ctx.tenant_id
        for permission in role.permissions
    }


@router.get("", response_model=APIResponse[list[APIKeyResponse]])
async def list_api_keys(ctx: APIKeysReadContext, db: DbSession):
    rows = await api_key_service.list_keys(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=[_response(r) for r in rows])


@router.post("", response_model=APIResponse[APIKeyCreated], status_code=status.HTTP_201_CREATED)
async def create_api_key(payload: APIKeyCreate, ctx: APIKeysCreateContext, db: DbSession):
    owner_permissions = _owner_permissions(ctx)
    edition_scopes = EDITION_SCOPE_ALLOWLIST_BY_KIND.get(ctx.tenant.tenant_kind, set())
    known_permission_rows = await db.execute(select(Permission.code))
    known_permission_codes = set(known_permission_rows.scalars().all())
    valid_scopes = known_permission_codes | edition_scopes

    if payload.scopes is None:
        # New keys default to the owner's current permissions, producing an
        # explicit least-privilege snapshot rather than inheriting future roles.
        if ctx.user.is_superuser:
            raise HTTPException(status_code=400, detail="Scopes are required for superuser API keys")
        scopes = sorted(owner_permissions)
    else:
        scopes = sorted(set(payload.scopes))
        if not scopes:
            raise HTTPException(status_code=400, detail="At least one API key scope is required")

    if not set(scopes).issubset(valid_scopes):
        raise HTTPException(status_code=400, detail="API key contains unknown or edition-incompatible scopes")
    requested_edition_names = {scope for scope in scopes if scope.startswith("edition.")}
    if not requested_edition_names.issubset(edition_scopes):
        raise HTTPException(status_code=400, detail="API key contains edition scopes incompatible with this tenant")
    # Edition scopes are not ordinary role permissions. Only a tenant
    # administrator may delegate them, and only for the tenant's own edition.
    requested_edition_scopes = set(scopes) & edition_scopes
    is_tenant_admin = ctx.user.is_superuser or any(
        role.tenant_id == ctx.tenant_id and role.name.lower() in {"admin", "owner", "tenant_admin"}
        for role in ctx.user.roles
    )
    if requested_edition_scopes and not is_tenant_admin:
        raise HTTPException(status_code=403, detail="Edition control-plane scopes require a tenant administrator")
    ordinary_scopes = set(scopes) - edition_scopes
    if not ctx.user.is_superuser and not ordinary_scopes.issubset(owner_permissions):
        raise HTTPException(status_code=403, detail="API key scope exceeds owner permissions")

    row, secret = await api_key_service.create_key(
        db, tenant_id=ctx.tenant_id, user_id=ctx.user_id,
        name=payload.name.strip(), expires_at=payload.expires_at, scopes=scopes
    )
    await audit_service.record(
        db, action="api_key.created", actor_type="user", actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id, resource_type="api_key", resource_id=row.id,
        request_id=request_id_var.get(),
        metadata={"name": row.name, "key_prefix": row.key_prefix, "scopes": row.scopes}
    )
    return APIResponse(success=True, data=APIKeyCreated(**_response(row).model_dump(), key=secret))


@router.post("/{key_id}/revoke", response_model=APIResponse[APIKeyResponse])
async def revoke_api_key(key_id: UUID, ctx: APIKeysRevokeContext, db: DbSession):
    row = await api_key_service.revoke_key(db, tenant_id=ctx.tenant_id, key_id=key_id)
    if row is None:
        raise HTTPException(status_code=404, detail="API key not found")
    await audit_service.record(
        db, action="api_key.revoked", actor_type="user", actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id, resource_type="api_key", resource_id=row.id,
        request_id=request_id_var.get(), metadata={"key_prefix": row.key_prefix}
    )
    return APIResponse(success=True, data=_response(row))

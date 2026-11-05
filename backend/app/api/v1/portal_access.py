"""Grant and revoke explicit access to direct child portals."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.deps import CurrentContext, DbSession
from app.core.security import create_access_token
from app.core.edition_deps import ResellerAdminContext, VendorAdminContext
from app.models.portal_access_grant import PortalAccessGrant
from app.models.tenant import Tenant
from app.schemas.common import APIResponse
from app.services import portal_access_service

router = APIRouter(prefix="/edition", tags=["portal-access"])


class PortalAccessGrantRequest(BaseModel):
    actor_user_id: UUID
    target_tenant_id: UUID
    reason: str = Field(min_length=1, max_length=2000)


def _serialize(grant: PortalAccessGrant) -> dict:
    return {
        "id": str(grant.id),
        "actor_user_id": str(grant.actor_user_id),
        "actor_tenant_id": str(grant.actor_tenant_id),
        "target_tenant_id": str(grant.target_tenant_id),
        "granted_by_user_id": str(grant.granted_by_user_id),
        "reason": grant.reason,
        "created_at": grant.created_at,
        "revoked_at": grant.revoked_at,
    }


def _reject_api_key(ctx) -> None:
    if ctx.api_key_id is not None:
        raise HTTPException(status_code=403, detail="Portal access grants require an interactive bearer session")


async def _create(payload: PortalAccessGrantRequest, ctx, db: DbSession):
    _reject_api_key(ctx)
    grant = await portal_access_service.create_portal_access_grant(
        db,
        grantor=ctx.user,
        actor_user_id=payload.actor_user_id,
        target_tenant_id=payload.target_tenant_id,
        reason=payload.reason,
    )
    return APIResponse(success=True, data=_serialize(grant))


async def _revoke(grant_id: UUID, ctx, db: DbSession):
    _reject_api_key(ctx)
    grant = await portal_access_service.revoke_portal_access_grant(
        db, grantor=ctx.user, grant_id=grant_id
    )
    return APIResponse(success=True, data=_serialize(grant))


async def _activate(grant_id: UUID, ctx, db: DbSession):
    _reject_api_key(ctx)
    grant = (await db.execute(
        select(PortalAccessGrant).where(
            PortalAccessGrant.id == grant_id,
            PortalAccessGrant.actor_user_id == ctx.user_id,
            PortalAccessGrant.actor_tenant_id == ctx.tenant_id,
            PortalAccessGrant.revoked_at.is_(None),
        )
    )).scalar_one_or_none()
    if grant is None:
        raise HTTPException(status_code=403, detail="An active user-bound portal grant is required")
    await portal_access_service.validate_portal_access_grant(
        db, actor_user_id=ctx.user_id, actor_tenant_id=ctx.tenant_id,
        target_tenant_id=grant.target_tenant_id, grant_id=grant.id,
    )
    target = (await db.execute(select(Tenant).where(Tenant.id == grant.target_tenant_id))).scalar_one()
    token = create_access_token(
        subject=ctx.user_id, tenant_id=ctx.tenant_id,
        extra_claims={
            "auth_token_version": ctx.user.auth_token_version,
            "portal_context_tenant_id": str(target.id),
            "portal_context_grant_id": str(grant.id),
            "portal_context_kind": target.tenant_kind,
        },
    )
    from app.services import audit_service
    await audit_service.record(
        db, tenant_id=ctx.tenant_id, actor_id=ctx.user_id,
        action="portal_access.context_activated", resource_type="portal_access_grant",
        resource_id=str(grant.id),
        metadata={"actor_tenant_id": str(ctx.tenant_id), "target_tenant_id": str(target.id)},
    )
    return APIResponse(success=True, data={"access_token": token, "token_type": "bearer", "context_tenant_id": str(target.id), "context_kind": target.tenant_kind})

async def _list(ctx, db: DbSession):
    _reject_api_key(ctx)
    rows = (await db.execute(
        select(PortalAccessGrant)
        .where(PortalAccessGrant.actor_tenant_id == ctx.tenant_id)
        .order_by(PortalAccessGrant.created_at.desc())
        .limit(200)
    )).scalars().all()
    return APIResponse(success=True, data=[_serialize(row) for row in rows])


@router.post("/vendor/portal-access-grants", status_code=201, response_model=APIResponse[dict])
async def create_vendor_portal_access_grant(payload: PortalAccessGrantRequest, ctx: VendorAdminContext, db: DbSession):
    return await _create(payload, ctx, db)


@router.get("/vendor/portal-access-grants", response_model=APIResponse[list[dict]])
async def list_vendor_portal_access_grants(ctx: VendorAdminContext, db: DbSession):
    return await _list(ctx, db)


@router.delete("/vendor/portal-access-grants/{grant_id}", response_model=APIResponse[dict])
async def revoke_vendor_portal_access_grant(grant_id: UUID, ctx: VendorAdminContext, db: DbSession):
    return await _revoke(grant_id, ctx, db)


@router.post("/reseller/portal-access-grants", status_code=201, response_model=APIResponse[dict])
async def create_reseller_portal_access_grant(payload: PortalAccessGrantRequest, ctx: ResellerAdminContext, db: DbSession):
    return await _create(payload, ctx, db)


@router.get("/reseller/portal-access-grants", response_model=APIResponse[list[dict]])
async def list_reseller_portal_access_grants(ctx: ResellerAdminContext, db: DbSession):
    return await _list(ctx, db)


@router.delete("/reseller/portal-access-grants/{grant_id}", response_model=APIResponse[dict])
async def revoke_reseller_portal_access_grant(grant_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    return await _revoke(grant_id, ctx, db)


@router.post("/vendor/portal-access-grants/{grant_id}/activate", response_model=APIResponse[dict])
async def activate_vendor_portal_context(grant_id: UUID, ctx: CurrentContext, db: DbSession):
    return await _activate(grant_id, ctx, db)


@router.post("/reseller/portal-access-grants/{grant_id}/activate", response_model=APIResponse[dict])
async def activate_reseller_portal_context(grant_id: UUID, ctx: CurrentContext, db: DbSession):
    return await _activate(grant_id, ctx, db)

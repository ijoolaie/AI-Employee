"""Manage explicit per-user Vendor/Reseller action grants."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.deps import DbSession
from app.core.edition_deps import ResellerAdminContext, VendorAdminContext
from app.models.tenant_action_grant import TenantActionGrant
from app.schemas.common import APIResponse
from app.services import tenant_action_grant_service

router = APIRouter(prefix="/edition", tags=["tenant-action-grants"])


class TenantActionGrantRequest(BaseModel):
    user_id: UUID
    action_code: str = Field(min_length=3, max_length=100)
    reason: str = Field(min_length=1, max_length=2000)
    expires_in_days: int = Field(default=90, ge=1, le=90)


def _serialize(grant: TenantActionGrant) -> dict:
    return {
        "id": str(grant.id),
        "user_id": str(grant.user_id),
        "tenant_id": str(grant.tenant_id),
        "action_code": grant.action_code,
        "granted_by_user_id": str(grant.granted_by_user_id),
        "reason": grant.reason,
        "created_at": grant.created_at,
        "expires_at": grant.expires_at,
        "revoked_at": grant.revoked_at,
    }


def _reject_api_key(ctx) -> None:
    if ctx.api_key_id is not None:
        raise HTTPException(status_code=403, detail="Action grants require an interactive bearer session")


async def _create(payload: TenantActionGrantRequest, ctx, db: DbSession):
    _reject_api_key(ctx)
    grant = await tenant_action_grant_service.create_tenant_action_grant(
        db,
        grantor=ctx.user,
        target_user_id=payload.user_id,
        action_code=payload.action_code,
        reason=payload.reason,
        expires_in_days=payload.expires_in_days,
    )
    return APIResponse(success=True, data=_serialize(grant))


async def _list(ctx, db: DbSession):
    _reject_api_key(ctx)
    rows = (await db.execute(
        select(TenantActionGrant)
        .where(TenantActionGrant.tenant_id == ctx.tenant_id)
        .order_by(TenantActionGrant.created_at.desc())
        .limit(500)
    )).scalars().all()
    return APIResponse(success=True, data=[_serialize(row) for row in rows])


async def _revoke(grant_id: UUID, ctx, db: DbSession):
    _reject_api_key(ctx)
    grant = await tenant_action_grant_service.revoke_tenant_action_grant(
        db, grantor=ctx.user, grant_id=grant_id
    )
    return APIResponse(success=True, data=_serialize(grant))


@router.post("/vendor/action-grants", status_code=201, response_model=APIResponse[dict])
async def create_vendor_action_grant(payload: TenantActionGrantRequest, ctx: VendorAdminContext, db: DbSession):
    return await _create(payload, ctx, db)


@router.get("/vendor/action-grants", response_model=APIResponse[list[dict]])
async def list_vendor_action_grants(ctx: VendorAdminContext, db: DbSession):
    return await _list(ctx, db)


@router.delete("/vendor/action-grants/{grant_id}", response_model=APIResponse[dict])
async def revoke_vendor_action_grant(grant_id: UUID, ctx: VendorAdminContext, db: DbSession):
    return await _revoke(grant_id, ctx, db)


@router.post("/reseller/action-grants", status_code=201, response_model=APIResponse[dict])
async def create_reseller_action_grant(payload: TenantActionGrantRequest, ctx: ResellerAdminContext, db: DbSession):
    return await _create(payload, ctx, db)


@router.get("/reseller/action-grants", response_model=APIResponse[list[dict]])
async def list_reseller_action_grants(ctx: ResellerAdminContext, db: DbSession):
    return await _list(ctx, db)


@router.delete("/reseller/action-grants/{grant_id}", response_model=APIResponse[dict])
async def revoke_reseller_action_grant(grant_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    return await _revoke(grant_id, ctx, db)

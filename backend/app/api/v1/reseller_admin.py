"""Reseller control-plane APIs for managing direct child client tenants."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.deps import CurrentContext, DbSession
from app.models.tenant import Tenant
from app.schemas.common import APIResponse

router = APIRouter(prefix="/reseller-admin", tags=["reseller-admin"])


class ClientTenantSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    tenant_kind: str
    created_at: datetime

    model_config = {"from_attributes": True}


async def require_reseller_admin(ctx: CurrentContext) -> None:
    if ctx.tenant.tenant_kind != "reseller":
        raise HTTPException(status_code=403, detail="Reseller workspace access required")
    if not ctx.user.is_superuser and not any(
        r.name.lower() in {"admin", "owner", "tenant_admin"} and r.tenant_id == ctx.tenant_id
        for r in ctx.user.roles
    ):
        raise HTTPException(status_code=403, detail="Reseller administrator access required")


@router.get("/clients", response_model=APIResponse[list[ClientTenantSummary]])
async def list_clients(ctx: CurrentContext, db: DbSession):
    await require_reseller_admin(ctx)
    result = await db.execute(
        select(Tenant)
        .where(Tenant.parent_tenant_id == ctx.tenant_id, Tenant.tenant_kind == "customer")
        .order_by(Tenant.created_at.desc())
    )
    clients = result.scalars().all()
    return APIResponse(success=True, data=[ClientTenantSummary.model_validate(t) for t in clients])


async def _get_client(client_id: UUID, ctx: CurrentContext, db: DbSession) -> Tenant:
    await require_reseller_admin(ctx)
    result = await db.execute(
        select(Tenant).where(
            Tenant.id == client_id,
            Tenant.parent_tenant_id == ctx.tenant_id,
            Tenant.tenant_kind == "customer",
        )
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client tenant not found")
    return client


@router.post("/clients/{client_id}/suspend", response_model=APIResponse[ClientTenantSummary])
async def suspend_client(client_id: UUID, ctx: CurrentContext, db: DbSession):
    client = await _get_client(client_id, ctx, db)
    client.status = "suspended"
    await db.commit()
    return APIResponse(success=True, data=ClientTenantSummary.model_validate(client))


@router.post("/clients/{client_id}/activate", response_model=APIResponse[ClientTenantSummary])
async def activate_client(client_id: UUID, ctx: CurrentContext, db: DbSession):
    client = await _get_client(client_id, ctx, db)
    client.status = "active"
    await db.commit()
    return APIResponse(success=True, data=ClientTenantSummary.model_validate(client))

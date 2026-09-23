"""CEO-controlled Internal Manager delegation API."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.workforce_delegation import WorkforceDelegation
from app.services import workforce_delegation_service as delegation_service

router = APIRouter(prefix="/workforce-delegations", tags=["workforce-delegations"])


class WorkforceDelegationCreate(BaseModel):
    manager_agent_instance_id: UUID
    starts_at: datetime
    expires_at: datetime
    allowed_operations: list[str] = Field(min_length=1, max_length=32)
    affected_employee_ids: list[UUID] = Field(default_factory=list, max_length=500)
    scope: dict = Field(default_factory=dict)
    resource_limits: dict = Field(default_factory=dict)
    risk_tier: int = Field(default=0, ge=0, le=4)
    revocation_conditions: list[str] = Field(default_factory=list, max_length=32)


class WorkforceDelegationRead(BaseModel):
    id: UUID
    tenant_id: UUID
    manager_agent_instance_id: UUID
    delegated_by_user_id: UUID
    scope: dict
    affected_employee_ids: list
    allowed_operations: list[str]
    resource_limits: dict
    risk_tier: int
    status: str
    starts_at: datetime
    expires_at: datetime
    revocation_conditions: list
    revoked_at: datetime | None
    revoked_by_user_id: UUID | None
    model_config = {"from_attributes": True}


class WorkforceDelegationRevoke(BaseModel):
    reason: str = Field(min_length=1, max_length=4000)


@router.post("", response_model=WorkforceDelegationRead, status_code=201)
async def create_workforce_delegation(
    payload: WorkforceDelegationCreate,
    ctx: TenantContext = Depends(require_permission("agent_workforce.ceo_approve")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await delegation_service.create_delegation(
            db, tenant_id=ctx.tenant_id, manager_agent_instance_id=payload.manager_agent_instance_id,
            delegated_by_user_id=ctx.user_id, starts_at=payload.starts_at, expires_at=payload.expires_at,
            allowed_operations=payload.allowed_operations,
            affected_employee_ids=[str(item) for item in payload.affected_employee_ids],
            scope=payload.scope, resource_limits=payload.resource_limits, risk_tier=payload.risk_tier,
            revocation_conditions=payload.revocation_conditions,
        )
        await db.commit()
        return item
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[WorkforceDelegationRead])
async def list_workforce_delegations(
    ctx: TenantContext = Depends(require_permission("agent_workforce.read")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    result = await db.execute(
        select(WorkforceDelegation).where(
            WorkforceDelegation.tenant_id == ctx.tenant_id
        ).order_by(WorkforceDelegation.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{delegation_id}/revoke", response_model=WorkforceDelegationRead)
async def revoke_workforce_delegation(
    delegation_id: UUID, payload: WorkforceDelegationRevoke,
    ctx: TenantContext = Depends(require_permission("agent_workforce.ceo_approve")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await delegation_service.revoke_delegation(
            db, tenant_id=ctx.tenant_id, delegation_id=delegation_id,
            revoked_by_user_id=ctx.user_id, reason=payload.reason,
        )
        await db.commit()
        return item
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

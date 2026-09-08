"""Stage 8 evaluation evidence and governed Agent control-plane endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.agent_access_review import AgentAccessReviewDecision
from app.models.agent_evaluation import AgentEvaluation, AgentEvaluationStatus
from app.models.agent_identity import AgentIdentity
from app.models.agent_kill_switch import AgentKillScope, AgentKillSwitch
from app.services.agent_governance import record_evaluation, review_access
from app.services.agent_kill_switch_service import assert_kill, revoke_kill
from app.services.agent_workforce_registry import list_workforce
from app.services.audit_service import record

router = APIRouter(prefix="/agent-governance", tags=["agent-governance"])


class AgentEvaluationCreate(BaseModel):
    suite_id: str = Field(min_length=1, max_length=120)
    status: AgentEvaluationStatus
    score: int | None = Field(default=None, ge=0, le=100)
    evidence: dict = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=4000)


class AgentEvaluationRead(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_template_id: UUID
    suite_id: str
    status: str
    score: int | None
    evidence: dict
    evidence_hash: str | None
    evaluator_user_id: UUID | None
    notes: str | None
    created_at: datetime


class AgentAccessReviewCreate(BaseModel):
    decision: AgentAccessReviewDecision
    next_review_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=4000)


class AgentAccessReviewRead(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_identity_id: UUID
    reviewer_user_id: UUID
    decision: str
    reviewed_at: datetime
    next_review_at: datetime | None
    reason: str | None


class AgentIdentityRead(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_instance_id: UUID
    owner_user_id: UUID
    sponsor_user_id: UUID
    subject: str
    expires_at: datetime | None
    revoked_at: datetime | None
    active: bool


class AgentKillSwitchCreate(BaseModel):
    scope: AgentKillScope
    reason: str = Field(min_length=1, max_length=500)
    agent_instance_id: UUID | None = None


class AgentKillSwitchRead(BaseModel):
    id: UUID
    tenant_id: UUID | None
    agent_instance_id: UUID | None
    scope: AgentKillScope
    active: bool
    reason: str
    asserted_by: UUID | None
    asserted_at: datetime
    revoked_at: datetime | None
    correlation_id: str


def _http(exc: Exception) -> HTTPException:
    text = str(exc)
    if "not found" in text.lower():
        return HTTPException(status_code=404, detail=text)
    if any(token in text.lower() for token in ("requires", "must", "lacks", "not authorized", "inactive", "expired", "cannot")):
        return HTTPException(status_code=422, detail=text)
    return HTTPException(status_code=409, detail=text)


@router.post("/templates/{template_id}/evaluate", response_model=AgentEvaluationRead, status_code=status.HTTP_201_CREATED)
async def evaluate_template(
    template_id: UUID,
    payload: AgentEvaluationCreate,
    ctx: TenantContext = Depends(require_permission("agent_template.evaluate")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await record_evaluation(
            db,
            tenant_id=ctx.tenant_id,
            template_id=template_id,
            suite_id=payload.suite_id,
            status=payload.status,
            evidence=payload.evidence,
            score=payload.score,
            evaluator_user_id=ctx.user_id,
            notes=payload.notes,
        )
        await record(db, action="agent_template.evaluated", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="agent_template", resource_id=template_id, metadata={"evaluation_id": str(item.id), "suite_id": item.suite_id, "status": item.status.value, "evidence_hash": item.evidence_hash})
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return AgentEvaluationRead.model_validate(item, from_attributes=True)


@router.get("/templates/{template_id}/evaluations", response_model=list[AgentEvaluationRead])
async def list_template_evaluations(
    template_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_template.read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentEvaluation)
        .where(AgentEvaluation.agent_template_id == template_id, AgentEvaluation.tenant_id == ctx.tenant_id)
        .order_by(AgentEvaluation.created_at.desc())
    )
    return [AgentEvaluationRead.model_validate(item, from_attributes=True) for item in result.scalars().all()]


@router.get("/workforce-registry")
async def workforce_registry(
    ctx: TenantContext = Depends(require_permission("agent_workforce.read")),
    db: AsyncSession = Depends(get_db),
):
    """Return the tenant's governed Agent workforce as one auditable projection."""
    return await list_workforce(db, tenant_id=ctx.tenant_id)


@router.get("/identities/{identity_id}", response_model=AgentIdentityRead)
async def get_identity(
    identity_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_instance.lifecycle")),
    db: AsyncSession = Depends(get_db),
):
    item = (await db.execute(select(AgentIdentity).where(AgentIdentity.id == identity_id, AgentIdentity.tenant_id == ctx.tenant_id))).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Agent identity not found")
    return AgentIdentityRead.model_validate(item, from_attributes=True)


@router.post("/identities/{identity_id}/access-review", response_model=AgentAccessReviewRead, status_code=status.HTTP_201_CREATED)
async def access_review(
    identity_id: UUID,
    payload: AgentAccessReviewCreate,
    ctx: TenantContext = Depends(require_permission("agent_instance.lifecycle")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await review_access(
            db,
            tenant_id=ctx.tenant_id,
            identity_id=identity_id,
            reviewer_user_id=ctx.user_id,
            decision=payload.decision,
            next_review_at=payload.next_review_at,
            reason=payload.reason,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return AgentAccessReviewRead.model_validate(item, from_attributes=True)


@router.post("/kill-switches", response_model=AgentKillSwitchRead, status_code=status.HTTP_201_CREATED)
async def create_kill_switch(
    payload: AgentKillSwitchCreate,
    ctx: TenantContext = Depends(require_permission("agent.emergency_kill")),
    db: AsyncSession = Depends(get_db),
):
    if payload.scope == AgentKillScope.GLOBAL:
        raise HTTPException(status_code=403, detail="Global emergency kill switch is system-operator only")
    try:
        item = await assert_kill(
            db,
            tenant_id=ctx.tenant_id,
            agent_instance_id=payload.agent_instance_id,
            scope=payload.scope,
            reason=payload.reason,
            asserted_by=ctx.user_id,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return AgentKillSwitchRead.model_validate(item, from_attributes=True)


@router.get("/kill-switches", response_model=list[AgentKillSwitchRead])
async def list_kill_switches(
    ctx: TenantContext = Depends(require_permission("agent.emergency_kill")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentKillSwitch)
        .where(AgentKillSwitch.tenant_id == ctx.tenant_id)
        .order_by(AgentKillSwitch.asserted_at.desc())
    )
    return [AgentKillSwitchRead.model_validate(item, from_attributes=True) for item in result.scalars().all()]


@router.post("/kill-switches/{kill_switch_id}/revoke", response_model=AgentKillSwitchRead)
async def revoke_kill_switch(
    kill_switch_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent.emergency_kill")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await revoke_kill(db, tenant_id=ctx.tenant_id, kill_switch_id=kill_switch_id, revoked_by=ctx.user_id)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return AgentKillSwitchRead.model_validate(item, from_attributes=True)

"""Stage 8 evaluation evidence and AgentIdentity access-review endpoints."""
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
from app.services.agent_governance import record_evaluation, review_access
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


def _http(exc: Exception) -> HTTPException:
    text = str(exc)
    if "not found" in text.lower():
        return HTTPException(status_code=404, detail=text)
    if "requires" in text.lower() or "must" in text.lower() or "lacks" in text.lower() or "not authorized" in text.lower():
        return HTTPException(status_code=422, detail=text)
    return HTTPException(status_code=409, detail=text)


@router.post("/templates/{template_id}/evaluate", response_model=AgentEvaluationRead, status_code=status.HTTP_201_CREATED)
async def evaluate_template(
    template_id: UUID,
    payload: AgentEvaluationCreate,
    ctx: TenantContext = Depends(require_permission("agent_template.create")),
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
    result = await db.execute(select(AgentEvaluation).where(AgentEvaluation.template_id if False else AgentEvaluation.agent_template_id == template_id, AgentEvaluation.tenant_id == ctx.tenant_id).order_by(AgentEvaluation.created_at.desc()))
    return [AgentEvaluationRead.model_validate(item, from_attributes=True) for item in result.scalars().all()]


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
        await record(db, action="agent_identity.access_reviewed", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="agent_identity", resource_id=identity_id, metadata={"review_id": str(item.id), "decision": item.decision.value, "next_review_at": item.next_review_at.isoformat() if item.next_review_at else None})
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return AgentAccessReviewRead.model_validate(item, from_attributes=True)

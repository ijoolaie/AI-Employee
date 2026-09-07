"""Governed dynamic workforce proposal and approval endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.agent_workforce_proposal import AgentWorkforceProposal, AgentWorkforceProposalStatus
from app.services import agent_workforce_proposal_service as proposal_service

router = APIRouter(prefix="/agent-workforce", tags=["agent-workforce"])


class WorkforceProposalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    rationale: str = Field(min_length=1, max_length=8000)
    requested_name: str = Field(min_length=1, max_length=255)
    sponsor_user_id: UUID
    agent_template_id: UUID | None = None
    agent_definition_id: UUID | None = None
    risk_tier: int = Field(default=0, ge=0, le=4)
    configuration: dict = Field(default_factory=dict)


class WorkforceDecision(BaseModel):
    approve: bool
    reason: str | None = Field(default=None, max_length=4000)


class WorkforceProposalRead(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_template_id: UUID | None
    agent_definition_id: UUID | None
    title: str
    rationale: str
    requested_name: str
    requester_user_id: UUID
    sponsor_user_id: UUID
    risk_tier: int
    configuration: dict
    status: AgentWorkforceProposalStatus
    board_reviewed_by: UUID | None
    board_decision_reason: str | None
    ceo_approved_by: UUID | None
    ceo_decision_reason: str | None
    provisioned_agent_instance_id: UUID | None
    created_at: datetime
    updated_at: datetime


def _http(exc: Exception) -> HTTPException:
    text = str(exc)
    if "not found" in text.lower():
        return HTTPException(status_code=404, detail=text)
    if any(token in text.lower() for token in ("requires", "must", "only", "independent", "match")):
        return HTTPException(status_code=422, detail=text)
    return HTTPException(status_code=409, detail=text)


@router.post("/proposals", response_model=WorkforceProposalRead, status_code=status.HTTP_201_CREATED)
async def create_workforce_proposal(
    payload: WorkforceProposalCreate,
    ctx: TenantContext = Depends(require_permission("agent_workforce.propose")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await proposal_service.create_proposal(
            db,
            tenant_id=ctx.tenant_id,
            requester_user_id=ctx.user_id,
            title=payload.title,
            rationale=payload.rationale,
            requested_name=payload.requested_name,
            sponsor_user_id=payload.sponsor_user_id,
            agent_template_id=payload.agent_template_id,
            agent_definition_id=payload.agent_definition_id,
            risk_tier=payload.risk_tier,
            configuration=payload.configuration,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return WorkforceProposalRead.model_validate(item, from_attributes=True)


@router.get("/proposals", response_model=list[WorkforceProposalRead])
async def list_workforce_proposals(
    status_filter: AgentWorkforceProposalStatus | None = None,
    ctx: TenantContext = Depends(require_permission("agent_workforce.read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AgentWorkforceProposal).where(AgentWorkforceProposal.tenant_id == ctx.tenant_id)
    if status_filter is not None:
        stmt = stmt.where(AgentWorkforceProposal.status == status_filter)
    result = await db.execute(stmt.order_by(AgentWorkforceProposal.created_at.desc()))
    return [WorkforceProposalRead.model_validate(item, from_attributes=True) for item in result.scalars().all()]


@router.post("/proposals/{proposal_id}/board-decision", response_model=WorkforceProposalRead)
async def board_decision(
    proposal_id: UUID,
    payload: WorkforceDecision,
    ctx: TenantContext = Depends(require_permission("agent_workforce.board_review")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await proposal_service.board_decide(db, tenant_id=ctx.tenant_id, proposal_id=proposal_id, reviewer_user_id=ctx.user_id, approve=payload.approve, reason=payload.reason)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return WorkforceProposalRead.model_validate(item, from_attributes=True)


@router.post("/proposals/{proposal_id}/ceo-decision", response_model=WorkforceProposalRead)
async def ceo_decision(
    proposal_id: UUID,
    payload: WorkforceDecision,
    ctx: TenantContext = Depends(require_permission("agent_workforce.ceo_approve")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await proposal_service.ceo_decide(db, tenant_id=ctx.tenant_id, proposal_id=proposal_id, approver_user_id=ctx.user_id, approve=payload.approve, reason=payload.reason)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return WorkforceProposalRead.model_validate(item, from_attributes=True)


@router.post("/proposals/{proposal_id}/provision", response_model=WorkforceProposalRead)
async def provision_workforce_proposal(
    proposal_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_workforce.provision")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await proposal_service.provision_approved_proposal(db, tenant_id=ctx.tenant_id, proposal_id=proposal_id)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return WorkforceProposalRead.model_validate(item, from_attributes=True)


@router.post("/proposals/{proposal_id}/activate", response_model=WorkforceProposalRead)
async def activate_workforce_proposal(
    proposal_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_workforce.activate")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await proposal_service.activate_provisioned_proposal(
            db,
            tenant_id=ctx.tenant_id,
            proposal_id=proposal_id,
            activated_by_user_id=ctx.user_id,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return WorkforceProposalRead.model_validate(item, from_attributes=True)

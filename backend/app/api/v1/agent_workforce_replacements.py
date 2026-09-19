"""Governed AgentInstance replacement endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.agent_workforce_proposal import AgentWorkforceProposal, AgentWorkforceProposalKind, AgentWorkforceProposalStatus
from app.services import agent_workforce_replacement_service as replacement_service
from app.services.agent_rollback import create_rollback_proposal

router = APIRouter(prefix="/agent-workforce/replacements", tags=["agent-workforce-replacements"])


class ReplacementProposalCreate(BaseModel):
    replacement_for_agent_instance_id: UUID
    agent_template_id: UUID
    title: str = Field(min_length=1, max_length=255)
    rationale: str = Field(min_length=1, max_length=8000)
    requested_name: str = Field(min_length=1, max_length=255)
    sponsor_user_id: UUID
    risk_tier: int = Field(ge=0, le=4)
    configuration: dict = Field(default_factory=dict)


class RollbackProposalCreate(BaseModel):
    agent_instance_id: UUID
    title: str = Field(min_length=1, max_length=255)
    rationale: str = Field(min_length=1, max_length=8000)
    requested_name: str = Field(min_length=1, max_length=255)
    sponsor_user_id: UUID
    configuration: dict = Field(default_factory=dict)


class ReplacementProposalRead(BaseModel):
    id: UUID
    tenant_id: UUID
    kind: AgentWorkforceProposalKind
    replacement_for_agent_instance_id: UUID | None
    provisioned_agent_instance_id: UUID | None
    status: AgentWorkforceProposalStatus
    requester_user_id: UUID
    sponsor_user_id: UUID
    agent_template_id: UUID | None
    agent_definition_id: UUID | None
    risk_tier: int
    replacement_cutover_at: datetime | None
    replacement_retired_at: datetime | None
    created_at: datetime
    updated_at: datetime


def _http(exc: Exception) -> HTTPException:
    text = str(exc)
    if "not found" in text.lower():
        return HTTPException(status_code=404, detail=text)
    if any(token in text.lower() for token in ("requires", "must", "only", "independent", "cannot", "still has")):
        return HTTPException(status_code=422, detail=text)
    return HTTPException(status_code=409, detail=text)


def _read(item: AgentWorkforceProposal) -> ReplacementProposalRead:
    return ReplacementProposalRead.model_validate(item, from_attributes=True)


@router.post("", response_model=ReplacementProposalRead, status_code=status.HTTP_201_CREATED)
async def create_replacement(
    payload: ReplacementProposalCreate,
    ctx: TenantContext = Depends(require_permission("agent_workforce.replace")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await replacement_service.create_replacement_proposal(
            db,
            tenant_id=ctx.tenant_id,
            requester_user_id=ctx.user_id,
            sponsor_user_id=payload.sponsor_user_id,
            replacement_for_agent_instance_id=payload.replacement_for_agent_instance_id,
            agent_template_id=payload.agent_template_id,
            title=payload.title,
            rationale=payload.rationale,
            requested_name=payload.requested_name,
            risk_tier=payload.risk_tier,
            configuration=payload.configuration,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return _read(item)


@router.post("/rollback", response_model=ReplacementProposalRead, status_code=status.HTTP_201_CREATED)
async def create_rollback(
    payload: RollbackProposalCreate,
    ctx: TenantContext = Depends(require_permission("agent_workforce.replace")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    """Create a governed rollback proposal without changing execution state."""
    try:
        item = await create_rollback_proposal(
            db,
            tenant_id=ctx.tenant_id,
            requester_user_id=ctx.user_id,
            sponsor_user_id=payload.sponsor_user_id,
            agent_instance_id=payload.agent_instance_id,
            title=payload.title,
            rationale=payload.rationale,
            requested_name=payload.requested_name,
            configuration=payload.configuration,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return _read(item)


@router.post("/{proposal_id}/prepare-cutover", response_model=ReplacementProposalRead)
async def prepare_cutover(
    proposal_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_workforce.replace")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await replacement_service.prepare_replacement_cutover(
            db,
            tenant_id=ctx.tenant_id,
            proposal_id=proposal_id,
            requested_by_user_id=ctx.user_id,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return _read(item)


@router.post("/{proposal_id}/cutover", response_model=ReplacementProposalRead)
async def cutover(
    proposal_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_workforce.replace")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await replacement_service.cutover_replacement(
            db,
            tenant_id=ctx.tenant_id,
            proposal_id=proposal_id,
            cutover_by_user_id=ctx.user_id,
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http(exc) from exc
    return _read(item)

"""Phase 13.4 immutable TeamEvaluation endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.team_evaluation import TeamEvaluation
from app.services.audit_service import record
from app.services.team_evaluation import TeamEvaluationError, TeamEvaluationService

router = APIRouter(prefix="/team-evaluations", tags=["team-evaluations"])
TeamEvaluationContext = TenantContext


class TeamEvaluationCreate(BaseModel):
    team_version_id: UUID
    evaluation_type: str = Field(min_length=1, max_length=80)
    score: float | None = Field(default=None, ge=0, le=1)
    input_data: dict = Field(default_factory=dict)
    output_data: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=4000)
    evidence_class: str = Field(default="engineering", max_length=32)


class TeamEvaluationRead(BaseModel):
    id: UUID
    tenant_id: UUID
    team_version_id: UUID
    evaluator_id: UUID | None
    evaluation_type: str
    score: float | None
    status: str
    evidence_class: str
    input_data: dict
    output_data: dict
    metrics: dict
    notes: str | None
    created_at: datetime


def _read(item: TeamEvaluation) -> TeamEvaluationRead:
    return TeamEvaluationRead.model_validate(item, from_attributes=True)


def _error(exc: TeamEvaluationError) -> HTTPException:
    message = str(exc)
    code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=message)


@router.post("", response_model=TeamEvaluationRead, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    payload: TeamEvaluationCreate,
    ctx: TenantContext = Depends(require_permission("team.evaluate")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await TeamEvaluationService(db).create(
            tenant_id=ctx.tenant_id,
            team_version_id=payload.team_version_id,
            evaluator_id=ctx.user_id,
            evaluation_type=payload.evaluation_type,
            score=payload.score,
            input_data=payload.input_data,
            output_data=payload.output_data,
            metrics=payload.metrics,
            notes=payload.notes,
            evidence_class=payload.evidence_class,
        )
        await record(
            db,
            action="team_evaluation.created",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="team_evaluation",
            resource_id=item.id,
            metadata={"team_version_id": str(item.team_version_id), "evidence_class": item.evidence_class},
        )
        await db.commit()
    except TeamEvaluationError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _read(item)


@router.get("", response_model=list[TeamEvaluationRead])
async def list_evaluations(
    ctx: TenantContext = Depends(require_permission("team.evaluate")),
    db: AsyncSession = Depends(get_db),
    team_version_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        items = await TeamEvaluationService(db).list(
            tenant_id=ctx.tenant_id, team_version_id=team_version_id, limit=limit, offset=offset
        )
    except TeamEvaluationError as exc:
        raise _error(exc) from exc
    return [_read(item) for item in items]


@router.get("/{evaluation_id}", response_model=TeamEvaluationRead)
async def get_evaluation(
    evaluation_id: UUID,
    ctx: TenantContext = Depends(require_permission("team.evaluate")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await TeamEvaluationService(db).get(tenant_id=ctx.tenant_id, evaluation_id=evaluation_id)
    except TeamEvaluationError as exc:
        raise _error(exc) from exc
    return _read(item)

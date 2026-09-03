"""Phase 13.2 authorized Agent Team installation endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TeamInstallContext
from app.models.team_installation import TeamInstallation
from app.services.audit_service import record
from app.services.team_installation import TeamInstallationError, TeamInstallationService

router = APIRouter(prefix="/team-installations", tags=["team-installations"])


class TeamInstallationCreate(BaseModel):
    team_version_id: UUID
    workspace_key: str | None = Field(default=None, max_length=120)


class TeamInstallationSummary(BaseModel):
    id: UUID
    tenant_id: UUID
    team_version_id: UUID
    workspace_key: str | None
    enabled: bool
    installed_by: UUID | None
    installed_at: datetime


def _summary(item: TeamInstallation) -> TeamInstallationSummary:
    return TeamInstallationSummary.model_validate(item, from_attributes=True)


def _error(exc: TeamInstallationError) -> HTTPException:
    message = str(exc)
    code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=message)


@router.post("", response_model=TeamInstallationSummary, status_code=status.HTTP_201_CREATED)
async def install_team(
    payload: TeamInstallationCreate,
    ctx: TeamInstallContext,
    db: AsyncSession = Depends(get_db),
):
    service = TeamInstallationService(db)
    try:
        installation = await service.install(
            tenant_id=ctx.tenant_id,
            team_version_id=payload.team_version_id,
            actor_id=ctx.user_id,
            workspace_key=payload.workspace_key,
        )
        await record(
            db,
            action="team_installation.created",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="team_installation",
            resource_id=installation.id,
            metadata={
                "team_version_id": str(installation.team_version_id),
                "workspace_key": installation.workspace_key,
            },
        )
        await db.commit()
    except TeamInstallationError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _summary(installation)


@router.get("", response_model=list[TeamInstallationSummary])
async def list_installations(
    ctx: TeamInstallContext,
    db: AsyncSession = Depends(get_db),
    workspace_key: str | None = Query(default=None, max_length=120),
    enabled: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    service = TeamInstallationService(db)
    try:
        items = await service.list(
            tenant_id=ctx.tenant_id,
            workspace_key=workspace_key,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )
    except TeamInstallationError as exc:
        raise _error(exc) from exc
    return [_summary(item) for item in items]


@router.get("/{installation_id}", response_model=TeamInstallationSummary)
async def get_installation(
    installation_id: UUID,
    ctx: TeamInstallContext,
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await TeamInstallationService(db).get(
            tenant_id=ctx.tenant_id,
            installation_id=installation_id,
        )
    except TeamInstallationError as exc:
        raise _error(exc) from exc
    return _summary(item)

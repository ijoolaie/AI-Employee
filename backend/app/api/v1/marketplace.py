"""Phase 13.5 marketplace publication, discovery and import endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.marketplace_publication import MarketplacePublication
from app.models.team_installation import TeamInstallation
from app.services.audit_service import record
from app.services.marketplace import MarketplaceError, MarketplaceService

router = APIRouter(prefix="/marketplace/publications", tags=["marketplace"])
MarketplacePublishContext = TenantContext
MarketplaceReadContext = TenantContext
MarketplaceInstallContext = TenantContext


class MarketplacePublicationCreate(BaseModel):
    team_version_id: UUID
    visibility: str = Field(default="private", pattern="^(private|unlisted|public)$")
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=2000)


class MarketplacePublicationRead(BaseModel):
    id: UUID
    owner_tenant_id: UUID
    team_version_id: UUID
    visibility: str
    status: str
    title: str
    summary: str | None
    published_by: UUID | None
    published_at: datetime
    withdrawn_at: datetime | None
    customer_acceptance: str = "not_implied"
    production_deployment: str = "not_implied"
    trust_basis: str = "recorded_evidence_only"


class MarketplaceInstallRequest(BaseModel):
    workspace_key: str | None = Field(default=None, max_length=120)


class MarketplaceInstallResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    team_version_id: UUID
    source_publication_id: UUID
    workspace_key: str | None
    enabled: bool
    installed_by: UUID | None
    installed_at: datetime


def _read(item: MarketplacePublication) -> MarketplacePublicationRead:
    return MarketplacePublicationRead.model_validate(item, from_attributes=True)


def _installation(item: TeamInstallation) -> MarketplaceInstallResponse:
    return MarketplaceInstallResponse.model_validate(item, from_attributes=True)


def _error(exc: MarketplaceError) -> HTTPException:
    message = str(exc)
    code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=message)


@router.post("", response_model=MarketplacePublicationRead, status_code=status.HTTP_201_CREATED)
async def publish_team_version(
    payload: MarketplacePublicationCreate,
    ctx: MarketplacePublishContext = Depends(require_permission("marketplace.publish")),
    db: AsyncSession = Depends(get_db),
):
    try:
        publication = await MarketplaceService(db).publish(
            owner_tenant_id=ctx.tenant_id,
            team_version_id=payload.team_version_id,
            actor_id=ctx.user_id,
            visibility=payload.visibility,
            title=payload.title,
            summary=payload.summary,
        )
        await record(
            db,
            action="marketplace_publication.created",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="marketplace_publication",
            resource_id=publication.id,
            metadata={
                "team_version_id": str(publication.team_version_id),
                "visibility": publication.visibility,
                "customer_acceptance": "not_implied",
                "production_deployment": "not_implied",
                "trust_basis": "recorded_evidence_only",
            },
        )
        await db.commit()
    except MarketplaceError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _read(publication)


@router.post("/{publication_id}/install", response_model=MarketplaceInstallResponse, status_code=status.HTTP_201_CREATED)
async def install_publication(
    publication_id: UUID,
    payload: MarketplaceInstallRequest,
    ctx: MarketplaceInstallContext = Depends(require_permission("marketplace.install")),
    db: AsyncSession = Depends(get_db),
):
    try:
        installation = await MarketplaceService(db).import_publication(
            tenant_id=ctx.tenant_id,
            publication_id=publication_id,
            actor_id=ctx.user_id,
            workspace_key=payload.workspace_key,
        )
        await record(
            db,
            action="marketplace_publication.installed",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="team_installation",
            resource_id=installation.id,
            metadata={
                "source_publication_id": str(publication_id),
                "team_version_id": str(installation.team_version_id),
                "workspace_key": installation.workspace_key,
                "customer_acceptance": "not_implied",
                "production_deployment": "not_implied",
                "trust_basis": "recorded_evidence_only",
            },
        )
        await db.commit()
    except MarketplaceError as exc:
        await db.rollback()
        raise _error(exc) from exc
    return _installation(installation)


@router.get("", response_model=list[MarketplacePublicationRead])
async def list_publications(
    ctx: MarketplaceReadContext = Depends(require_permission("marketplace.read")),
    db: AsyncSession = Depends(get_db),
    visibility: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        items = await MarketplaceService(db).list_for_tenant(
            tenant_id=ctx.tenant_id, visibility=visibility, limit=limit, offset=offset
        )
    except MarketplaceError as exc:
        raise _error(exc) from exc
    return [_read(item) for item in items]


@router.get("/{publication_id}", response_model=MarketplacePublicationRead)
async def get_publication(
    publication_id: UUID,
    ctx: MarketplaceReadContext = Depends(require_permission("marketplace.read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await MarketplaceService(db).get_for_tenant(tenant_id=ctx.tenant_id, publication_id=publication_id)
    except MarketplaceError as exc:
        raise _error(exc) from exc
    return _read(item)

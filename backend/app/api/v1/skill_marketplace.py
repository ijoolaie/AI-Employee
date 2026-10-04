"""W16 third-party SkillPackage publication and discovery endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from uuid import UUID

from app.core.deps import DbSession, TenantContext, require_permission
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.schemas.common import APIResponse
from app.schemas.skill_marketplace_publication import (
    SkillMarketplacePublicationCreate,
    SkillMarketplacePublicationResponse,
)
from app.services.audit_service import record
from app.services.skill_marketplace_publication_service import (
    SkillMarketplacePublicationError,
    SkillMarketplacePublicationService,
)

router = APIRouter(prefix="/skill-marketplace/publications", tags=["skill-marketplace"])

SkillMarketplacePublishContext = TenantContext


def _read(item: SkillMarketplacePublication) -> SkillMarketplacePublicationResponse:
    return SkillMarketplacePublicationResponse.model_validate(item, from_attributes=True)


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, SkillMarketplacePublicationError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    from app.core.exceptions import NotFoundError
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "",
    response_model=APIResponse[SkillMarketplacePublicationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def publish_skill_package(
    payload: SkillMarketplacePublicationCreate,
    ctx: SkillMarketplacePublishContext = __import__("fastapi").Depends(require_permission("skill_marketplace.publish")),
    db: DbSession = None,
):
    try:
        publication = await SkillMarketplacePublicationService.publish(
            db,
            owner_tenant_id=ctx.tenant_id,
            skill_package_id=payload.skill_package_id,
            actor_id=ctx.user_id,
            visibility=payload.visibility,
            title=payload.title,
            summary=payload.summary,
        )
        await record(
            db,
            action="skill_marketplace_publication.created",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="skill_marketplace_publication",
            resource_id=publication.id,
            metadata={
                "skill_package_id": str(publication.skill_package_id),
                "visibility": publication.visibility,
                "presentation_only": True,
                "installation": "not_implied",
                "execution_authority_changed": False,
                "customer_acceptance": "not_implied",
                "trust_basis": "recorded_evidence_only",
            },
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _error(exc) from exc
    return APIResponse(success=True, data=_read(publication))


@router.get(
    "",
    response_model=APIResponse[list[SkillMarketplacePublicationResponse]],
)
async def list_skill_publications(
    ctx: TenantContext = __import__("fastapi").Depends(require_permission("skill_marketplace.read")),
    db: DbSession = None,
    visibility: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        items = await SkillMarketplacePublicationService.list_for_tenant(
            db,
            tenant_id=ctx.tenant_id,
            visibility=visibility,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise _error(exc) from exc
    return APIResponse(success=True, data=[_read(item) for item in items])


@router.get(
    "/{publication_id}",
    response_model=APIResponse[SkillMarketplacePublicationResponse],
)
async def get_skill_publication(
    publication_id: UUID,
    ctx: TenantContext = __import__("fastapi").Depends(require_permission("skill_marketplace.read")),
    db: DbSession = None,
):
    try:
        item = await SkillMarketplacePublicationService.get_for_tenant(
            db,
            tenant_id=ctx.tenant_id,
            publication_id=publication_id,
        )
    except Exception as exc:
        raise _error(exc) from exc
    return APIResponse(success=True, data=_read(item))

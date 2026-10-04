"""W16 third-party SkillPackage publication and discovery endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DbSession, TenantContext, require_permission
from app.core.exceptions import NotFoundError
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.schemas.common import APIResponse
from app.schemas.skill_marketplace_publication import (
    SkillMarketplacePublicationCreate,
    SkillMarketplacePublicationResponse,
)
from app.schemas.skill_marketplace_purchase import SkillMarketplacePurchaseCreate, SkillMarketplacePurchaseResponse
from app.services.skill_marketplace_purchase_service import create_checkout
from app.services.audit_service import record
from app.services.skill_marketplace_publication_service import (
    SkillMarketplacePublicationError,
    SkillMarketplacePublicationService,
)

router = APIRouter(prefix="/skill-marketplace/publications", tags=["skill-marketplace"])

SkillMarketplacePublishContext = TenantContext
SkillMarketplaceReadContext = TenantContext


def _read(item: SkillMarketplacePublication) -> SkillMarketplacePublicationResponse:
    return SkillMarketplacePublicationResponse.model_validate(item, from_attributes=True)


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, SkillMarketplacePublicationError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "",
    response_model=APIResponse[SkillMarketplacePublicationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def publish_skill_package(
    payload: SkillMarketplacePublicationCreate,
    db: DbSession,
    ctx: SkillMarketplacePublishContext = Depends(require_permission("skill_marketplace.publish")),
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
    db: DbSession,
    ctx: SkillMarketplaceReadContext = Depends(require_permission("skill_marketplace.read")),
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
    db: DbSession,
    ctx: SkillMarketplaceReadContext = Depends(require_permission("skill_marketplace.read")),
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


@router.post(
    "/purchases",
    response_model=APIResponse[SkillMarketplacePurchaseResponse],
    status_code=status.HTTP_201_CREATED,
)
async def purchase_skill_package(
    payload: SkillMarketplacePurchaseCreate,
    db: DbSession,
    ctx: SkillMarketplaceReadContext = Depends(require_permission("skill_marketplace.purchase")),
):
    try:
        purchase, deal, payment, replay = await create_checkout(
            db,
            buyer_tenant_id=ctx.tenant_id,
            employee_id=payload.employee_id,
            publication_id=payload.publication_id,
            actor_id=ctx.user_id,
            customer_email=getattr(ctx.user, "email", None),
            idempotency_key=payload.idempotency_key,
        )
    except Exception as exc:
        await db.rollback()
        raise _error(exc) from exc

    provider = payment.provider if payment is not None else (purchase.provider or "none")
    provider_execution = payment.provider_execution if payment is not None else "settled"
    executed = payment.executed if payment is not None else True
    checkout_url = payment.checkout_url if payment is not None else None
    provider_payment_id = payment.provider_payment_id if payment is not None else None

    return APIResponse(
        success=True,
        data=SkillMarketplacePurchaseResponse(
            purchase_id=purchase.id,
            deal_id=deal.id,
            status=purchase.status.value,
            provider=provider,
            provider_execution=provider_execution,
            executed=executed,
            checkout_url=checkout_url,
            provider_payment_id=provider_payment_id,
            buyer_tenant_id=purchase.buyer_tenant_id,
            seller_tenant_id=purchase.seller_tenant_id,
            employee_id=purchase.employee_id,
            skill_package_id=purchase.skill_package_id,
            product_id=purchase.product_id,
            amount=str(purchase.amount),
            currency=purchase.currency,
            idempotent_replay=replay,
        ),
    )

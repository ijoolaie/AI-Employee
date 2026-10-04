"""Third-party SkillPackage publication and discovery boundary for W16."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.models.skill_package import SkillPackage, SkillPackageStatus
from app.services.skill_marketplace_service import (
    _validate_manifest,
    _validate_product_contract,
    _validate_skill_metadata,
)


class SkillMarketplacePublicationError(ConflictError):
    """Raised when a third-party skill publication invariant is violated."""


class SkillMarketplacePublicationService:
    """Publication is discovery metadata; installation/execution remain separate gates."""

    VISIBILITIES = {"private", "unlisted", "public"}

    @staticmethod
    async def _load_publishable_package(
        db: AsyncSession,
        *,
        owner_tenant_id: uuid.UUID,
        skill_package_id: uuid.UUID,
    ) -> SkillPackage:
        result = await db.execute(
            select(SkillPackage).where(
                SkillPackage.id == skill_package_id,
                SkillPackage.tenant_id == owner_tenant_id,
                SkillPackage.status == SkillPackageStatus.PUBLISHED,
            )
        )
        package = result.scalar_one_or_none()
        if package is None:
            raise NotFoundError("published skill package not found")

        _validate_manifest(package.manifest or {})
        _validate_skill_metadata(package.compatibility or {}, "skill compatibility")
        _validate_skill_metadata(package.presentation_metadata or {}, "skill presentation metadata")

        product = None
        if package.product_id is not None:
            product = (
                await db.execute(
                    select(Product).where(
                        Product.id == package.product_id,
                        Product.tenant_id == owner_tenant_id,
                    )
                )
            ).scalar_one_or_none()
        _validate_product_contract(product, package)
        return package

    @classmethod
    async def publish(
        cls,
        db: AsyncSession,
        *,
        owner_tenant_id: uuid.UUID,
        skill_package_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        visibility: str,
        title: str,
        summary: str | None = None,
    ) -> SkillMarketplacePublication:
        visibility = visibility.strip().lower()
        title = title.strip()
        if visibility not in cls.VISIBILITIES:
            raise SkillMarketplacePublicationError("publication visibility is invalid")
        if not title or len(title) > 255:
            raise SkillMarketplacePublicationError("publication title is invalid")
        if summary is not None and len(summary) > 2000:
            raise SkillMarketplacePublicationError("publication summary is invalid")

        package = await cls._load_publishable_package(
            db,
            owner_tenant_id=owner_tenant_id,
            skill_package_id=skill_package_id,
        )

        existing = await db.execute(
            select(SkillMarketplacePublication).where(
                SkillMarketplacePublication.skill_package_id == package.id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise SkillMarketplacePublicationError("skill package is already published to the marketplace")

        publication = SkillMarketplacePublication(
            owner_tenant_id=owner_tenant_id,
            skill_package_id=package.id,
            visibility=visibility,
            title=title,
            summary=summary,
            published_by=actor_id,
        )
        db.add(publication)
        try:
            await db.flush()
        except IntegrityError as exc:
            raise SkillMarketplacePublicationError(
                "skill package is already published to the marketplace"
            ) from exc

        return publication

    @classmethod
    async def get_for_tenant(
        cls,
        db: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        publication_id: uuid.UUID,
    ) -> SkillMarketplacePublication:
        result = await db.execute(
            select(SkillMarketplacePublication).where(
                SkillMarketplacePublication.id == publication_id,
                (
                    (SkillMarketplacePublication.owner_tenant_id == tenant_id)
                    | (SkillMarketplacePublication.visibility == "public")
                ),
            )
        )
        publication = result.scalar_one_or_none()
        if publication is None:
            raise NotFoundError("skill marketplace publication not found")
        return publication

    @classmethod
    async def list_for_tenant(
        cls,
        db: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        visibility: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SkillMarketplacePublication]:
        if limit < 1 or limit > 200:
            raise SkillMarketplacePublicationError("publication limit must be between 1 and 200")
        if offset < 0:
            raise SkillMarketplacePublicationError("publication offset cannot be negative")
        if visibility is not None:
            visibility = visibility.strip().lower()
            if visibility not in cls.VISIBILITIES:
                raise SkillMarketplacePublicationError("publication visibility is invalid")

        stmt = select(SkillMarketplacePublication).where(
            (SkillMarketplacePublication.owner_tenant_id == tenant_id)
            | (SkillMarketplacePublication.visibility == "public")
        )
        if visibility is not None:
            if visibility == "public":
                stmt = stmt.where(SkillMarketplacePublication.visibility == "public")
            else:
                stmt = stmt.where(
                    SkillMarketplacePublication.owner_tenant_id == tenant_id,
                    SkillMarketplacePublication.visibility == visibility,
                )
        stmt = stmt.order_by(
            SkillMarketplacePublication.published_at.desc(),
            SkillMarketplacePublication.id.desc(),
        ).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


__all__ = [
    "SkillMarketplacePublicationError",
    "SkillMarketplacePublicationService",
]

"""Tenant-safe marketplace publication and discovery boundary."""
from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_publication import MarketplacePublication
from app.models.team_definition import TeamDefinition
from app.models.team_version import TeamVersion


class MarketplaceError(RuntimeError):
    """Raised when marketplace ownership or visibility rules are violated."""


class MarketplaceService:
    """Publication is discovery metadata only; installation remains explicit and authorized."""

    VISIBILITIES = {"private", "unlisted", "public"}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish(
        self,
        *,
        owner_tenant_id: uuid.UUID,
        team_version_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        visibility: str,
        title: str,
        summary: str | None = None,
    ) -> MarketplacePublication:
        visibility = visibility.strip().lower()
        title = title.strip()
        if visibility not in self.VISIBILITIES:
            raise MarketplaceError("publication visibility is invalid")
        if not title or len(title) > 255:
            raise MarketplaceError("publication title is invalid")
        if summary is not None and len(summary) > 2000:
            raise MarketplaceError("publication summary is invalid")

        result = await self.db.execute(
            select(TeamVersion, TeamDefinition)
            .join(TeamDefinition, TeamDefinition.id == TeamVersion.team_id)
            .where(TeamVersion.id == team_version_id)
        )
        row = result.one_or_none()
        if row is None:
            raise MarketplaceError("team version not found")
        version, team = row
        if team.tenant_id != owner_tenant_id:
            raise MarketplaceError("only the owning tenant may publish this team version")
        if not team.enabled:
            raise MarketplaceError("team definition is disabled")
        if version.version < 1 or not version.member_agent_definition_ids:
            raise MarketplaceError("team version is not publishable")

        existing = await self.db.execute(
            select(MarketplacePublication).where(MarketplacePublication.team_version_id == team_version_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise MarketplaceError("team version is already published")

        publication = MarketplacePublication(
            owner_tenant_id=owner_tenant_id,
            team_version_id=team_version_id,
            visibility=visibility,
            status="published",
            title=title,
            summary=summary,
            published_by=actor_id,
        )
        self.db.add(publication)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            raise MarketplaceError("team version is already published") from exc
        return publication

    async def get_for_tenant(self, *, tenant_id: uuid.UUID, publication_id: uuid.UUID) -> MarketplacePublication:
        result = await self.db.execute(
            select(MarketplacePublication).where(
                MarketplacePublication.id == publication_id,
                MarketplacePublication.status == "published",
                (MarketplacePublication.owner_tenant_id == tenant_id)
                | (MarketplacePublication.visibility == "public"),
            )
        )
        publication = result.scalar_one_or_none()
        if publication is None:
            raise MarketplaceError("marketplace publication not found")
        return publication

    async def list_for_tenant(
        self,
        *,
        tenant_id: uuid.UUID,
        visibility: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MarketplacePublication]:
        if limit < 1 or limit > 200:
            raise MarketplaceError("publication limit must be between 1 and 200")
        if offset < 0:
            raise MarketplaceError("publication offset cannot be negative")
        if visibility is not None:
            visibility = visibility.strip().lower()
            if visibility not in self.VISIBILITIES:
                raise MarketplaceError("publication visibility is invalid")
        stmt = select(MarketplacePublication).where(
            MarketplacePublication.status == "published",
            (MarketplacePublication.owner_tenant_id == tenant_id)
            | (MarketplacePublication.visibility == "public"),
        )
        if visibility is not None:
            stmt = stmt.where(MarketplacePublication.visibility == visibility)
        stmt = stmt.order_by(MarketplacePublication.published_at.desc(), MarketplacePublication.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

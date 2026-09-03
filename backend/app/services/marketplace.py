"""Tenant-safe marketplace publication, discovery and import boundary."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_definition import AgentDefinition
from app.models.marketplace_publication import MarketplacePublication
from app.models.team_definition import TeamDefinition
from app.models.team_installation import TeamInstallation
from app.models.team_version import TeamVersion


class MarketplaceError(RuntimeError):
    """Raised when marketplace ownership or visibility rules are violated."""


class MarketplaceService:
    """Publication is discovery metadata; import creates a tenant-local package."""

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

    async def import_publication(
        self,
        *,
        tenant_id: uuid.UUID,
        publication_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        workspace_key: str | None = None,
    ) -> TeamInstallation:
        """Import a public publication as a fully tenant-local immutable package.

        AgentDefinitions are copied rather than referenced across tenants. This
        preserves the runtime's existing tenant checks and makes the installed
        TeamVersion independent from future edits in the publisher tenant.
        AgentInstances are intentionally not created; provisioning remains a
        tenant-local operational responsibility.
        """
        if workspace_key is not None and (not workspace_key.strip() or len(workspace_key) > 120):
            raise MarketplaceError("workspace key is invalid")
        workspace_key = workspace_key.strip() if workspace_key else None

        publication_result = await self.db.execute(
            select(MarketplacePublication, TeamVersion, TeamDefinition)
            .join(TeamVersion, TeamVersion.id == MarketplacePublication.team_version_id)
            .join(TeamDefinition, TeamDefinition.id == TeamVersion.team_id)
            .where(
                MarketplacePublication.id == publication_id,
                MarketplacePublication.status == "published",
                (MarketplacePublication.owner_tenant_id == tenant_id)
                | (MarketplacePublication.visibility == "public"),
            )
        )
        row = publication_result.one_or_none()
        if row is None:
            raise MarketplaceError("marketplace publication not found")
        publication, source_version, source_team = row
        if not source_team.enabled or source_version.version < 1 or not source_version.member_agent_definition_ids:
            raise MarketplaceError("marketplace publication is not importable")

        existing = await self.db.execute(
            select(TeamInstallation).where(
                TeamInstallation.tenant_id == tenant_id,
                TeamInstallation.source_publication_id == publication_id,
                TeamInstallation.workspace_key == workspace_key,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise MarketplaceError("marketplace publication is already installed in this scope")

        try:
            source_ids = [uuid.UUID(str(item)) for item in source_version.member_agent_definition_ids]
        except (TypeError, ValueError) as exc:
            raise MarketplaceError("marketplace publication contains an invalid agent definition id") from exc

        agent_result = await self.db.execute(
            select(AgentDefinition).where(
                AgentDefinition.tenant_id == source_team.tenant_id,
                AgentDefinition.id.in_(source_ids),
                AgentDefinition.enabled.is_(True),
            )
        )
        source_agents = {agent.id: agent for agent in agent_result.scalars().all()}
        if len(source_agents) != len(source_ids):
            raise MarketplaceError("marketplace publication references unavailable agent definitions")

        imported_agent_ids: list[str] = []
        for source_id in source_ids:
            source_agent = source_agents[source_id]
            slug_base = f"{source_agent.slug}-marketplace-{publication.id.hex[:8]}"
            slug = slug_base[:120]
            imported_agent = AgentDefinition(
                tenant_id=tenant_id,
                slug=slug,
                name=source_agent.name,
                description=source_agent.description,
                version=source_agent.version,
                capabilities=source_agent.capabilities or [],
                allowed_tools=source_agent.allowed_tools or [],
                model_policy=source_agent.model_policy or {},
                input_schema=source_agent.input_schema or {},
                output_schema=source_agent.output_schema or {},
                policy_requirements=source_agent.policy_requirements or {},
                enabled=True,
            )
            self.db.add(imported_agent)
            await self.db.flush()
            imported_agent_ids.append(str(imported_agent.id))

        team_slug = f"{source_team.slug}-marketplace-{publication.id.hex[:8]}"[:120]
        imported_team = TeamDefinition(
            tenant_id=tenant_id,
            slug=team_slug,
            name=source_team.name,
            description=source_team.description,
            enabled=True,
        )
        self.db.add(imported_team)
        await self.db.flush()

        imported_version = TeamVersion(
            team_id=imported_team.id,
            version=source_version.version,
            member_agent_definition_ids=imported_agent_ids,
            roles=source_version.roles or {},
            execution_policy=source_version.execution_policy or {},
            allowed_tools=source_version.allowed_tools or [],
            input_schema=source_version.input_schema or {},
            output_schema=source_version.output_schema or {},
        )
        self.db.add(imported_version)
        await self.db.flush()

        installation = TeamInstallation(
            tenant_id=tenant_id,
            team_version_id=imported_version.id,
            source_publication_id=publication_id,
            workspace_key=workspace_key,
            installed_by=actor_id,
            enabled=True,
        )
        self.db.add(installation)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            raise MarketplaceError("marketplace publication is already installed in this scope") from exc
        return installation

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

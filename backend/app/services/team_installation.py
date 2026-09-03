"""Authorized tenant-local installation boundary for Agent Teams."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_definition import TeamDefinition
from app.models.team_installation import TeamInstallation
from app.models.team_version import TeamVersion


class TeamInstallationError(RuntimeError):
    """Raised when a team installation violates its tenant/lifecycle contract."""


class TeamInstallationService:
    """Tenant-bound installation service; never accepts an untrusted target tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def install(
        self,
        *,
        tenant_id: uuid.UUID,
        team_version_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        workspace_key: str | None = None,
    ) -> TeamInstallation:
        """Install an enabled team version into its owning tenant.

        P13.2 is deliberately pre-marketplace: cross-tenant package import is
        rejected until the later publication/import boundary exists. The
        installation record is only a local binding and grants no control-plane
        authority beyond the already-owned TeamVersion.
        """
        if workspace_key is not None and (not workspace_key.strip() or len(workspace_key) > 120):
            raise TeamInstallationError("workspace key is invalid")
        workspace_key = workspace_key.strip() if workspace_key else None

        result = await self.db.execute(
            select(TeamVersion, TeamDefinition)
            .join(TeamDefinition, TeamDefinition.id == TeamVersion.team_id)
            .where(TeamVersion.id == team_version_id)
        )
        row = result.one_or_none()
        if row is None:
            raise TeamInstallationError("team version not found")
        version, team = row

        if team.tenant_id != tenant_id:
            raise TeamInstallationError("cross-tenant team installation is not available before marketplace import")
        if not team.enabled:
            raise TeamInstallationError("team definition is disabled")
        if version.version < 1:
            raise TeamInstallationError("team version is invalid")
        if not version.member_agent_definition_ids:
            raise TeamInstallationError("team version has no members")

        existing = await self.db.execute(
            select(TeamInstallation).where(
                TeamInstallation.tenant_id == tenant_id,
                TeamInstallation.team_version_id == team_version_id,
                TeamInstallation.workspace_key == workspace_key,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise TeamInstallationError("team version is already installed in this scope")

        installation = TeamInstallation(
            tenant_id=tenant_id,
            team_version_id=team_version_id,
            workspace_key=workspace_key,
            installed_by=actor_id,
            enabled=True,
        )
        self.db.add(installation)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            raise TeamInstallationError("team version is already installed in this scope") from exc
        return installation

    async def get(
        self,
        *,
        tenant_id: uuid.UUID,
        installation_id: uuid.UUID,
    ) -> TeamInstallation:
        result = await self.db.execute(
            select(TeamInstallation).where(
                TeamInstallation.id == installation_id,
                TeamInstallation.tenant_id == tenant_id,
            )
        )
        installation = result.scalar_one_or_none()
        if installation is None:
            raise TeamInstallationError("team installation not found")
        return installation

    async def list(
        self,
        *,
        tenant_id: uuid.UUID,
        workspace_key: str | None = None,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TeamInstallation]:
        if limit < 1 or limit > 200:
            raise TeamInstallationError("installation limit must be between 1 and 200")
        if offset < 0:
            raise TeamInstallationError("installation offset cannot be negative")
        stmt = select(TeamInstallation).where(TeamInstallation.tenant_id == tenant_id)
        if workspace_key is not None:
            stmt = stmt.where(TeamInstallation.workspace_key == workspace_key)
        if enabled is not None:
            stmt = stmt.where(TeamInstallation.enabled.is_(enabled))
        stmt = stmt.order_by(TeamInstallation.installed_at.desc(), TeamInstallation.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

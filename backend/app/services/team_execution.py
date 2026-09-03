"""WorkItem-backed Agent Team execution orchestration."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import request_id_var
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.team_definition import TeamDefinition
from app.models.team_installation import TeamInstallation
from app.models.team_version import TeamVersion
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.agent_execution_adapter import AgentExecutionAdapter
from app.services.schema_validation import validate_json_data


class TeamExecutionError(ValueError):
    """Raised when a team cannot be safely dispatched."""


class TeamExecutionService:
    """Dispatch an installed team through the canonical WorkItem/Run substrate."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        installation_id: uuid.UUID,
        input_data: dict[str, Any],
        actor_id: uuid.UUID | None,
        idempotency_key: str,
        title: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        if not idempotency_key.strip():
            raise TeamExecutionError("idempotency_key is required")
        if len(idempotency_key) > 255:
            raise TeamExecutionError("idempotency_key is too long")

        result = await self.db.execute(
            select(TeamInstallation, TeamVersion, TeamDefinition)
            .join(TeamVersion, TeamVersion.id == TeamInstallation.team_version_id)
            .join(TeamDefinition, TeamDefinition.id == TeamVersion.team_id)
            .where(
                TeamInstallation.id == installation_id,
                TeamInstallation.tenant_id == tenant_id,
                TeamInstallation.enabled.is_(True),
                TeamDefinition.tenant_id == tenant_id,
                TeamDefinition.enabled.is_(True),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise TeamExecutionError("team installation not found")
        installation, version, team = row
        if not version.member_agent_definition_ids:
            raise TeamExecutionError("team version has no members")

        validate_json_data(input_data, version.input_schema, field_name="input_data")

        request_id = correlation_id or request_id_var.get()
        parent = WorkItem(
            tenant_id=tenant_id,
            title=title or f"Execute team {team.slug} v{version.version}",
            description=team.description,
            status=WorkItemStatus.RUNNING,
            requester_id=actor_id,
            input_data=input_data,
            policy_context={
                "team_installation_id": str(installation.id),
                "team_version_id": str(version.id),
                "team_id": str(team.id),
                "correlation_id": request_id,
                "execution_policy": version.execution_policy or {},
                "allowed_tools": version.allowed_tools or [],
            },
            idempotency_key=f"team:{installation.id}:{idempotency_key}",
        )
        self.db.add(parent)
        await self.db.flush()

        dispatches: list[dict[str, Any]] = []
        adapter = AgentExecutionAdapter(self.db)
        for position, definition_id in enumerate(version.member_agent_definition_ids):
            try:
                definition_uuid = uuid.UUID(str(definition_id))
            except (TypeError, ValueError) as exc:
                raise TeamExecutionError("team version contains an invalid agent definition id") from exc

            instance_result = await self.db.execute(
                select(AgentInstance)
                .where(
                    AgentInstance.tenant_id == tenant_id,
                    AgentInstance.agent_definition_id == definition_uuid,
                    AgentInstance.enabled.is_(True),
                    AgentInstance.status == AgentInstanceStatus.ENABLED,
                )
                .order_by(AgentInstance.created_at, AgentInstance.id)
                .limit(1)
            )
            agent = instance_result.scalar_one_or_none()
            if agent is None:
                raise TeamExecutionError(f"no enabled agent instance for team member {definition_id}")

            child = WorkItem(
                tenant_id=tenant_id,
                title=f"{parent.title} — member {position + 1}",
                description=f"Team member {definition_id}",
                status=WorkItemStatus.ASSIGNED,
                requester_id=actor_id,
                executor_type=ExecutorType.AGENT,
                executor_id=agent.id,
                input_data=input_data,
                policy_context={
                    "team_work_item_id": str(parent.id),
                    "team_installation_id": str(installation.id),
                    "team_version_id": str(version.id),
                    "member_position": position,
                    "correlation_id": request_id,
                },
                idempotency_key=f"team:{installation.id}:{idempotency_key}:member:{position}",
                parent_work_item_id=parent.id,
            )
            self.db.add(child)
            await self.db.flush()
            dispatch = await adapter.dispatch(child, agent)
            dispatches.append({"work_item_id": str(child.id), **dispatch})

        return {
            "work_item_id": str(parent.id),
            "team_installation_id": str(installation.id),
            "team_version_id": str(version.id),
            "status": parent.status.value,
            "correlation_id": request_id,
            "members": dispatches,
        }

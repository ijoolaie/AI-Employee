"""Bridge specialized Agent execution into the existing Employee/Run runtime."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tool_registry import registry
from app.models.agent_instance import AgentInstance
from app.models.work_item import WorkItem
from app.services.agent_governance import assert_agent_can_execute
from app.services.agent_runtime_binding import resolve_employee_version
from app.services.run_service import create_run


class AgentExecutionAdapter:
    """Create canonical Runs and enforce AgentInstance execution authority."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(self, work_item: WorkItem, agent: AgentInstance) -> dict[str, Any]:
        instance, definition, version = await resolve_employee_version(
            self.db,
            tenant_id=work_item.tenant_id,
            agent_instance_id=agent.id,
        )
        run = await create_run(
            self.db,
            tenant_id=work_item.tenant_id,
            employee_id=version.employee_id,
            employee_version_id=version.id,
            input_data=work_item.input_data or {},
            created_by=work_item.requester_id,
        )
        return {
            "run_id": str(run.id),
            "executor_type": "agent",
            "agent_instance_id": str(instance.id),
            "agent_definition_id": str(definition.id),
            "employee_id": str(version.employee_id),
            "employee_version_id": str(version.id),
        }

    async def execute_tool(
        self,
        *,
        agent: AgentInstance,
        tool_name: str,
        arguments: dict[str, Any],
        approval_granted: bool = False,
    ) -> Any:
        """Execute a Tool only after AgentInstance identity/policy checks."""
        tool = registry.get(tool_name)
        await assert_agent_can_execute(
            self.db,
            tenant_id=agent.tenant_id,
            agent_instance_id=agent.id,
            tool_name=tool_name,
            required_permission=tool.required_permission,
        )
        return await registry.execute(
            tool_name,
            arguments,
            permissions=set((agent.permission_policy or {}).get("permissions") or []),
            approval_granted=approval_granted,
            allowed_tools=set((agent.permission_policy or {}).get("allowed_tools") or (agent.permission_policy or {}).get("tools") or []),
            db=self.db,
            tenant_id=agent.tenant_id,
        )

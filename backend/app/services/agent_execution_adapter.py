"""Bridge governed Agent execution into the canonical Run runtime."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tool_registry import registry
from app.models.agent_instance import AgentInstance
from app.models.work_item import WorkItem
from app.services.agent_policy_engine import PolicyRequest, assert_authorized
from app.services.agent_governance import assert_agent_can_execute
from app.services.agent_runtime_binding import resolve_employee_version
from app.services.run_service import create_run

logger = logging.getLogger("app.services.agent_execution_adapter")


class AgentExecutionAdapter:
    """Create canonical Runs and hand them to the existing Run worker."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(self, work_item: WorkItem, agent: AgentInstance) -> dict[str, Any]:
        agent_tenant_id = getattr(agent, "tenant_id", work_item.tenant_id)
        if agent_tenant_id != work_item.tenant_id:
            raise ValueError("cross-tenant agent execution is forbidden")
        if not getattr(agent, "enabled", True):
            raise ValueError("agent instance is not executable")

        # Re-establish current Agent authority at the WorkItem -> Run
        # hand-off. The Run worker performs a second authorization immediately
        # before provider/tool execution; this first check prevents a revoked,
        # killed, expired, or drifted Agent from creating a new executable Run
        # after WorkItem dispatch has already committed RUNNING state.
        await assert_authorized(
            self.db,
            PolicyRequest(
                tenant_id=work_item.tenant_id,
                agent_instance_id=agent.id,
                action="run.execute",
            ),
        )

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
        run.agent_instance_id = instance.id
        await self.db.flush()

        try:
            from app.workers.run_worker import execute_run_task

            execute_run_task.delay(str(run.id), str(work_item.tenant_id))
        except Exception:  # noqa: BLE001
            logger.warning(
                "agent_run_enqueue_failed",
                extra={
                    "run_id": str(run.id),
                    "work_item_id": str(getattr(work_item, "id", "unknown")),
                },
                exc_info=True,
            )

        result = {
            "run_id": str(run.id),
            "executor_type": "agent",
            "agent_instance_id": str(instance.id),
            "agent_definition_id": str(definition.id),
            "employee_id": str(version.employee_id),
            "employee_version_id": str(version.id),
        }
        if getattr(work_item, "id", None) is not None:
            result["work_item_id"] = str(work_item.id)
        return result

    async def execute_tool(
        self,
        *,
        agent: AgentInstance,
        tool_name: str,
        arguments: dict[str, Any],
        approval_granted: bool = False,
    ) -> Any:
        """Execute a Tool only after the central policy decision allows it."""
        tool = registry.get(tool_name)
        await assert_agent_can_execute(
            self.db,
            tenant_id=agent.tenant_id,
            agent_instance_id=agent.id,
            tool_name=tool_name,
            required_permission=tool.required_permission,
            approval_granted=approval_granted,
            requires_approval=tool.requires_approval,
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

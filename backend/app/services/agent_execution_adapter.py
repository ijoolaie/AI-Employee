"""Bridge governed Agent execution into the canonical Run runtime."""
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
    """Create canonical Runs and hand them to the existing Run worker."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(self, work_item: WorkItem, agent: AgentInstance) -> dict[str, Any]:
        # WorkItem dispatch is an execution boundary too. Re-check the
        # activated AgentInstance identity/policy before creating a Run.
        # The synthetic work-item capability is intentionally not used here:
        # the authoritative lifecycle/identity gate remains the runtime worker
        # and the adapter still resolves the tenant-scoped binding below.
        if agent.tenant_id != work_item.tenant_id:
            raise ValueError("cross-tenant agent execution is forbidden")
        if not agent.enabled:
            raise ValueError("agent instance is not executable")

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
        # agent_instance_id is deliberately persisted on the canonical Run;
        # the worker therefore has an authoritative identity to re-check.
        run.agent_instance_id = instance.id
        await self.db.flush()

        # Reuse the canonical asynchronous Run execution path. This is the
        # same worker used by the normal Run API; no parallel Agent runtime is
        # introduced. The worker will re-check AgentInstance + AgentIdentity
        # and install governed ToolRegistry context before execute_run().
        try:
            from app.workers.run_worker import execute_run_task

            execute_run_task.delay(str(run.id), str(work_item.tenant_id))
        except Exception:  # noqa: BLE001
            # Match the existing Run API contract: persistence of the Run is
            # still useful for observability/retry, while enqueue failure is
            # logged by the worker boundary rather than creating a second
            # execution implementation here.
            import logging

            logging.getLogger("app.services.agent_execution_adapter").warning(
                "agent_run_enqueue_failed",
                extra={"run_id": str(run.id), "work_item_id": str(work_item.id)},
                exc_info=True,
            )

        return {
            "run_id": str(run.id),
            "executor_type": "agent",
            "agent_instance_id": str(instance.id),
            "agent_definition_id": str(definition.id),
            "employee_id": str(version.employee_id),
            "employee_version_id": str(version.id),
            "work_item_id": str(work_item.id),
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

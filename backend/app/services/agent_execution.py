"""Canonical Agent executor bridging WorkItems to Employee Runs."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_instance import AgentInstance
from app.models.work_item import WorkItem
from app.services import run_service
from app.services.agent_runtime_binding import resolve_employee_version
from app.workers.run_worker import execute_run_task


class AgentExecutionAdapter:
    """Create exactly one tenant-scoped Run for an assigned Agent WorkItem."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(self, work_item: WorkItem, agent: AgentInstance) -> dict[str, Any]:
        if agent.tenant_id != work_item.tenant_id:
            raise RuntimeError("cross-tenant agent execution is forbidden")

        instance, _definition, version = await resolve_employee_version(
            self.db,
            tenant_id=work_item.tenant_id,
            agent_instance_id=agent.id,
        )

        run = await run_service.create_run(
            self.db,
            tenant_id=work_item.tenant_id,
            employee_id=version.employee_id,
            employee_version_id=version.id,
            input_data=work_item.input_data or {},
            created_by=work_item.requester_id,
        )

        # Persist the Run before exposing it to the asynchronous worker.
        await self.db.commit()
        execute_run_task.delay(str(run.id), str(work_item.tenant_id))

        return {
            "run_id": str(run.id),
            "employee_version_id": str(version.id),
            "agent_instance_id": str(instance.id),
        }

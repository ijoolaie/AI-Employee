from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timezone
import uuid
from typing import Any
from app.shared.events import DomainEvent
from app.shared.event_catalog import WORKFLOW_RUN_COMPLETED
from app.modules.workflow.domain.models import WorkflowRun
from app.modules.workflow.domain.ports import WorkflowExecutor, WorkflowRunRepository

class WorkflowApplicationService:
    def __init__(
        self,
        repository: WorkflowRunRepository,
        executor: WorkflowExecutor,
        event_bus,
    ) -> None:
        self.repository = repository
        self.executor = executor
        self.event_bus = event_bus

    async def run(
        self,
        *,
        workflow_id: str,
        payload: dict[str, Any],
        tenant_id: uuid.UUID | None = None,
    ) -> WorkflowRun:
        now = datetime.now(timezone.utc)
        run = WorkflowRun(
            id=uuid.uuid4(),
            workflow_id=uuid.UUID(workflow_id),
            tenant_id=tenant_id,
            status="running",
            input=payload,
            output=None,
            started_at=now,
        )
        await self.repository.save(run)
        try:
            output = await self.executor.execute(workflow_id, payload)
            completed = replace(
                run,
                status="completed",
                output=output,
                completed_at=datetime.now(timezone.utc),
            )
            completed = await self.repository.save(completed)
            await self.event_bus.publish(
                DomainEvent(
                    name=WORKFLOW_RUN_COMPLETED,
                    tenant_id=tenant_id,
                    payload={"run_id": str(completed.id), "workflow_id": workflow_id},
                )
            )
            return completed
        except Exception:
            failed = replace(run, status="failed", completed_at=datetime.now(timezone.utc))
            await self.repository.save(failed)
            raise

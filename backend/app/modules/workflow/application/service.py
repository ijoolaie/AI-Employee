from __future__ import annotations
from datetime import datetime, timezone
import uuid
from typing import Any, Awaitable, Callable

from app.modules.workflow.domain.models import WorkflowRun
from app.modules.workflow.domain.ports import WorkflowExecutor, WorkflowRunRepository


class WorkflowApplicationService:
    """
    Application boundary for workflow execution requests.

    Important: this service must not execute workflows directly.
    Actual execution is owned by the governed workflow worker path
    (lease + outbox + retry safety). This prevents duplicate execution
    paths from entering the system.
    """

    def __init__(
        self,
        repository: WorkflowRunRepository,
        executor: WorkflowExecutor | None = None,
        event_bus=None,
        enqueue_execution: Callable[[WorkflowRun], Awaitable[None]] | None = None,
    ) -> None:
        self.repository = repository
        self.executor = executor
        self.event_bus = event_bus
        self.enqueue_execution = enqueue_execution

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

        run = await self.repository.save(run)

        if self.enqueue_execution is None:
            raise RuntimeError(
                "Governed workflow execution enqueue is not configured"
            )

        await self.enqueue_execution(run)
        return run

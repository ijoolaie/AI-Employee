"""Runtime adapter for human-owned WorkItems."""
from __future__ import annotations

from typing import Any

from app.models.work_item import ExecutorType, WorkItem
from app.services.unified_execution import ExecutionError


class HumanExecutionAdapter:
    """Marks a WorkItem as actively awaiting its assigned human executor."""

    def dispatch(self, work_item: WorkItem) -> dict[str, Any]:
        if work_item.executor_type is not ExecutorType.HUMAN or work_item.executor_id is None:
            raise ExecutionError("work item has no human executor")
        return {
            "executor_type": ExecutorType.HUMAN.value,
            "executor_id": str(work_item.executor_id),
            "state": "awaiting_human",
        }

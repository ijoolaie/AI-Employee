"""Lightweight human execution adapter for the canonical WorkItem path."""
from __future__ import annotations

from typing import Any

from app.models.work_item import WorkItem


class HumanExecutionAdapter:
    """Record human dispatch without pretending the human work is complete.

    Human work is completed explicitly through the human completion lifecycle;
    dispatch only moves the WorkItem into the RUNNING state.
    """

    async def dispatch(self, work_item: WorkItem) -> dict[str, Any]:
        return {
            "executor_type": "human",
            "executor_id": str(work_item.executor_id),
            "status": "dispatched",
        }

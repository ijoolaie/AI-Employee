"""Human execution adapter for the unified WorkItem runtime."""

from __future__ import annotations

from typing import Any

from app.models.work_item import WorkItem


class HumanExecutionAdapter:
    """Dispatch adapter that exposes an assigned WorkItem to a human executor."""

    def dispatch(self, work_item: WorkItem) -> dict[str, Any]:
        return {
            "executor": "human",
            "work_item_id": str(work_item.id),
            "status": "awaiting_human_action",
        }

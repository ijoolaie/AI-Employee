"""Tenant-safe operator attention queue for the Platform Command Center."""

from __future__ import annotations

from typing import Any


_PRIORITY = {
    "failed": 0,
    "waiting_approval": 1,
    "running": 2,
    "pending": 3,
}


def attention_queue(work_items: list[Any], *, tenant_id: Any, actor_tenant_id: Any) -> list[dict[str, Any]]:
    if tenant_id != actor_tenant_id:
        raise PermissionError("command center tenant mismatch")

    queue = []
    for item in work_items:
        if getattr(item, "tenant_id", None) != tenant_id:
            continue
        status = getattr(getattr(item, "status", None), "value", str(getattr(item, "status", "")))
        if status not in _PRIORITY:
            continue
        queue.append(
            {
                "work_item_id": str(getattr(item, "id")),
                "correlation_id": getattr(item, "correlation_id", None),
                "status": status,
                "executor_type": getattr(getattr(item, "executor_type", None), "value", str(getattr(item, "executor_type", ""))),
                "priority": _PRIORITY[status],
            }
        )

    return sorted(queue, key=lambda entry: (entry["priority"], entry["work_item_id"]))

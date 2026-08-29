"""Safe next-action readiness for Platform Command Center operators."""

from __future__ import annotations

from typing import Any


_ACTIONS = {
    "failed": ["inspect_failure", "retry"],
    "waiting_approval": ["review_approval"],
    "running": ["inspect_progress"],
    "pending": ["inspect_queue"],
}


def action_readiness(work_items: list[Any], *, tenant_id: Any, actor_tenant_id: Any) -> list[dict[str, Any]]:
    if tenant_id != actor_tenant_id:
        raise PermissionError("command center tenant mismatch")

    results = []
    for item in work_items:
        if getattr(item, "tenant_id", None) != tenant_id:
            continue
        status = getattr(getattr(item, "status", None), "value", str(getattr(item, "status", "")))
        actions = _ACTIONS.get(status)
        if not actions:
            continue
        results.append(
            {
                "work_item_id": str(getattr(item, "id")),
                "correlation_id": getattr(item, "correlation_id", None),
                "status": status,
                "actions": actions,
            }
        )
    return results

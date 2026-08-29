"""Tenant-safe chronological action timeline for Platform Command Center."""

from __future__ import annotations

from typing import Any


def action_timeline(
    events: list[dict[str, Any]], *, tenant_id: Any, actor_tenant_id: Any
) -> list[dict[str, Any]]:
    if tenant_id != actor_tenant_id:
        raise PermissionError("tenant mismatch")

    visible = []
    for event in events:
        if str(event.get("tenant_id")) != str(tenant_id):
            continue
        visible.append(
            {
                "work_item_id": event.get("work_item_id"),
                "correlation_id": event.get("correlation_id"),
                "action": event.get("action"),
                "status": event.get("status", "recorded"),
                "recorded_at": event.get("recorded_at"),
            }
        )

    return sorted(visible, key=lambda event: event.get("recorded_at") or "")

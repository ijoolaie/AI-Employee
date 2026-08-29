"""Safe correlation drilldown projection for the Platform workspace."""

from __future__ import annotations

from typing import Any


_ALLOWED_ROLES = {"viewer", "operator", "admin"}
_SAFE_FIELDS = {"work_item_id", "correlation_id", "status", "priority", "reason", "evidence_ref", "audit_ref"}


def workspace_drilldown(summary: dict[str, Any], *, work_item_id: str, role: str) -> dict[str, Any] | None:
    if role not in _ALLOWED_ROLES:
        return None
    for item in summary.get("attention", []):
        if item.get("work_item_id") == work_item_id:
            result = {key: item[key] for key in _SAFE_FIELDS if key in item}
            result["read_only"] = role == "viewer"
            return result
    return None

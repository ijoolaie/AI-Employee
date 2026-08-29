"""Tenant-safe execution overview for the Platform Command Center."""

from __future__ import annotations

from collections import Counter
from typing import Any


_SECRET_MARKERS = ("secret", "password", "token", "credential", "api_key")


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _safe(item)
            for key, item in value.items()
            if not any(marker in key.lower() for marker in _SECRET_MARKERS)
        }
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def execution_overview(work_items: list[Any], *, tenant_id: Any, actor_tenant_id: Any) -> dict[str, Any]:
    if tenant_id != actor_tenant_id:
        raise PermissionError("command center tenant mismatch")

    items = [item for item in work_items if getattr(item, "tenant_id", None) == tenant_id]
    statuses = Counter(getattr(getattr(item, "status", None), "value", str(getattr(item, "status", ""))) for item in items)
    executors = Counter(getattr(getattr(item, "executor_type", None), "value", str(getattr(item, "executor_type", ""))) for item in items)

    evidence = []
    for item in items:
        output = getattr(item, "output_data", None)
        if isinstance(output, dict):
            evidence.append({"work_item_id": str(getattr(item, "id")), "output": _safe(output)})

    return {
        "tenant_id": str(tenant_id),
        "total_work_items": len(items),
        "lifecycle": dict(statuses),
        "executor_mix": dict(executors),
        "waiting_approval": statuses.get("waiting_approval", 0),
        "failed": statuses.get("failed", 0),
        "evidence": evidence,
    }

"""Tenant-safe result projection for Platform Command Center actions."""

from __future__ import annotations

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


def action_result(
    *,
    tenant_id: Any,
    actor_tenant_id: Any,
    work_item_id: Any,
    correlation_id: str | None,
    action: str,
    succeeded: bool,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if tenant_id != actor_tenant_id:
        raise PermissionError("tenant mismatch")

    return {
        "tenant_id": str(tenant_id),
        "work_item_id": str(work_item_id),
        "correlation_id": correlation_id,
        "action": action,
        "status": "succeeded" if succeeded else "failed",
        "result": _safe(result or {}),
    }

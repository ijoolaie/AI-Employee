"""Tenant-safe correlation drilldown for Platform Command Center."""

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


def correlation_drilldown(
    events: list[dict[str, Any]],
    *,
    tenant_id: Any,
    actor_tenant_id: Any,
    correlation_id: str,
) -> list[dict[str, Any]]:
    if tenant_id != actor_tenant_id:
        raise PermissionError("tenant mismatch")

    matches = [
        _safe(event)
        for event in events
        if str(event.get("tenant_id")) == str(tenant_id)
        and event.get("correlation_id") == correlation_id
    ]
    return sorted(matches, key=lambda event: event.get("recorded_at") or "")

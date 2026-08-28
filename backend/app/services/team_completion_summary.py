"""Operator-facing completion summary for Agent Team runs."""

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


def summarize_team_run(run: Any, *, actor_tenant_id: Any) -> dict[str, Any]:
    """Return a tenant-safe completion projection for operators."""
    if getattr(run, "tenant_id", None) != actor_tenant_id:
        raise PermissionError("team run tenant mismatch")

    required = sorted(getattr(run, "required_members", set()))
    completed = sorted(getattr(run, "completed_members", set()))
    evidence = _safe(list(getattr(run, "evidence", [])))

    return {
        "run_id": str(getattr(run, "id")),
        "tenant_id": str(getattr(run, "tenant_id")),
        "correlation_id": getattr(run, "correlation_id"),
        "status": getattr(getattr(run, "status"), "value", str(getattr(run, "status"))),
        "required_members": required,
        "completed_members": completed,
        "pending_members": sorted(set(required) - set(completed)),
        "is_complete": set(required) <= set(completed),
        "evidence": evidence,
    }

"""Tenant-safe operational health projection for Agent Team runs."""

from __future__ import annotations

from typing import Any


def team_health(run: Any, *, actor_tenant_id: Any) -> dict[str, Any]:
    if getattr(run, "tenant_id", None) != actor_tenant_id:
        raise PermissionError("team run tenant mismatch")

    status = getattr(getattr(run, "status", None), "value", str(getattr(run, "status", "")))
    required = set(getattr(run, "required_members", set()))
    completed = set(getattr(run, "completed_members", set()))
    blocked = sorted(required - completed)

    waiting_approval = status == "waiting_approval"
    failed = status == "failed"
    ready = not failed and not waiting_approval and not blocked

    return {
        "tenant_id": str(getattr(run, "tenant_id")),
        "run_id": str(getattr(run, "id")),
        "correlation_id": getattr(run, "correlation_id"),
        "status": status,
        "blocked_members": blocked,
        "waiting_approval": waiting_approval,
        "failed": failed,
        "ready": ready,
    }

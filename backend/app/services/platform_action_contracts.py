"""Validation contracts for Platform Command Center operator actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_ALLOWED = {
    "failed": {"inspect_failure", "retry"},
    "waiting_approval": {"review_approval"},
    "running": {"inspect_progress"},
    "pending": {"inspect_queue"},
}


@dataclass(frozen=True)
class PlatformActionRequest:
    tenant_id: Any
    work_item_id: Any
    correlation_id: str | None
    action: str


def validate_action(item: Any, request: PlatformActionRequest, *, actor_tenant_id: Any) -> PlatformActionRequest:
    if actor_tenant_id != request.tenant_id or getattr(item, "tenant_id", None) != request.tenant_id:
        raise PermissionError("tenant mismatch")
    if str(getattr(item, "id")) != str(request.work_item_id):
        raise ValueError("work item mismatch")

    status = getattr(getattr(item, "status", None), "value", str(getattr(item, "status", "")))
    if request.action not in _ALLOWED.get(status, set()):
        raise ValueError("action not allowed for current state")
    return request

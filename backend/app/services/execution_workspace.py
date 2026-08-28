"""Safe UI-facing projections for the unified execution workspace."""

from __future__ import annotations

from typing import Any
from uuid import UUID


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


class ExecutionWorkspace:
    """Tenant-scoped projection boundary for operator-facing execution state."""

    @staticmethod
    def project(*, tenant_id: UUID, actor_tenant_id: UUID, work_item: Any, telemetry: list[Any] | None = None) -> dict[str, Any]:
        if tenant_id != actor_tenant_id:
            raise PermissionError("workspace tenant mismatch")

        events = []
        for event in telemetry or []:
            if getattr(event, "tenant_id", None) == tenant_id and getattr(event, "work_item_id", None) == work_item.id:
                events.append(
                    {
                        "event": event.event,
                        "duration_ms": event.duration_ms,
                        "cost": event.cost,
                        "tokens": event.tokens,
                        "correlation_id": event.correlation_id,
                        "metadata": _safe(event.metadata or {}),
                    }
                )

        policy = _safe(getattr(work_item, "policy_context", None) or {})
        return {
            "tenant_id": str(tenant_id),
            "work_item_id": str(work_item.id),
            "status": getattr(work_item.status, "value", str(work_item.status)),
            "executor_type": getattr(getattr(work_item, "executor_type", None), "value", getattr(work_item, "executor_type", None)),
            "executor_id": str(getattr(work_item, "executor_id", "")) or None,
            "waiting_for_approval": getattr(work_item.status, "value", str(work_item.status)) == "waiting_approval",
            "policy": policy,
            "telemetry": events,
        }

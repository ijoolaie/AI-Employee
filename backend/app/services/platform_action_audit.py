"""Secret-safe audit projection for Platform Command Center operator actions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_SECRET_MARKERS = ("secret", "password", "token", "credential", "api_key")


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    return {
        key: value
        for key, value in (metadata or {}).items()
        if not any(marker in key.lower() for marker in _SECRET_MARKERS)
    }


def action_audit_record(
    *,
    tenant_id: Any,
    actor_tenant_id: Any,
    work_item_id: Any,
    correlation_id: str | None,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if tenant_id != actor_tenant_id:
        raise PermissionError("tenant mismatch")

    return {
        "tenant_id": str(tenant_id),
        "work_item_id": str(work_item_id),
        "correlation_id": correlation_id,
        "action": action,
        "metadata": _safe_metadata(metadata),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

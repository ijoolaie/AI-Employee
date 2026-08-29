"""Role-aware Platform workspace contract built on the Phase 9 operator model."""

from __future__ import annotations

from typing import Any

from app.services.platform_operator_summary import operator_summary


_ALLOWED_ROLES = {"platform_admin", "platform_operator"}


def platform_workspace_summary(
    work_items: list[Any], *, tenant_id: Any, actor_tenant_id: Any, actor_role: str
) -> dict[str, Any]:
    if actor_role not in _ALLOWED_ROLES:
        raise PermissionError("platform workspace role required")
    return operator_summary(work_items, tenant_id=tenant_id, actor_tenant_id=actor_tenant_id)

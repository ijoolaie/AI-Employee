"""Permission helpers for the Platform workspace surface."""

from __future__ import annotations

_ALLOWED_ROLES = frozenset({"platform_admin", "platform_operator"})


def can_view_command_center(*, actor_role: str, actor_tenant_id, tenant_id) -> bool:
    return actor_role in _ALLOWED_ROLES and actor_tenant_id == tenant_id

"""Compact tenant-safe operator model for the Platform Command Center."""

from __future__ import annotations

from typing import Any

from app.services.platform_action_readiness import action_readiness
from app.services.platform_attention_queue import attention_queue
from app.services.platform_command_center import execution_overview


def operator_summary(
    work_items: list[Any], *, tenant_id: Any, actor_tenant_id: Any
) -> dict[str, Any]:
    overview = execution_overview(
        work_items, tenant_id=tenant_id, actor_tenant_id=actor_tenant_id
    )
    attention = attention_queue(
        work_items, tenant_id=tenant_id, actor_tenant_id=actor_tenant_id
    )
    actions = action_readiness(
        work_items, tenant_id=tenant_id, actor_tenant_id=actor_tenant_id
    )

    return {
        "overview": overview,
        "attention": attention,
        "action_readiness": actions,
        "attention_count": len(attention),
        "actionable_count": len(actions),
    }

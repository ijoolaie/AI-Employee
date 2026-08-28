"""Workspace-facing execution presentation contracts."""

from __future__ import annotations

from typing import Any
from uuid import UUID


class WorkspaceExecutionView:
    """Build a UI-ready, tenant-safe execution summary."""

    @staticmethod
    def from_work_item(work_item: Any, *, actor_tenant_id: UUID) -> dict[str, Any]:
        if work_item.tenant_id != actor_tenant_id:
            raise PermissionError("workspace tenant mismatch")

        policy = getattr(work_item, "policy_context", {}) or {}
        output = getattr(work_item, "output_data", None)
        safe_policy = {
            key: value
            for key, value in policy.items()
            if "secret" not in key.lower() and "password" not in key.lower()
        }

        return {
            "work_item_id": str(work_item.id),
            "tenant_id": str(work_item.tenant_id),
            "status": getattr(work_item.status, "value", str(work_item.status)),
            "executor_type": getattr(getattr(work_item, "executor_type", None), "value", None),
            "executor_id": str(work_item.executor_id) if getattr(work_item, "executor_id", None) else None,
            "approval_required": bool(policy.get("requires_approval")),
            "approved": bool(policy.get("approved")),
            "policy": safe_policy,
            "delegation": {
                "parent_work_item_id": str(work_item.parent_work_item_id)
                if getattr(work_item, "parent_work_item_id", None)
                else None,
                "handoff_target_agent_id": policy.get("handoff_target_agent_id"),
            },
            "has_output": output is not None,
        }

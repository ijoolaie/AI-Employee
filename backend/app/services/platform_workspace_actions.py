"""Role-aware action panel projection for the Platform workspace."""

from __future__ import annotations

from typing import Any


_READ_ONLY = {"viewer"}
_ALLOWED = {"inspect_failure", "retry", "review_approval", "inspect_progress", "inspect_queue"}


def workspace_actions(summary: dict[str, Any], *, role: str) -> list[dict[str, Any]]:
    """Project safe operator actions without executing them."""
    actions: list[dict[str, Any]] = []
    for item in summary.get("action_readiness", []):
        for action in item.get("actions", []):
            if action not in _ALLOWED:
                continue
            actions.append({
                "work_item_id": item.get("work_item_id"),
                "action": action,
                "enabled": role not in _READ_ONLY,
            })
    return actions

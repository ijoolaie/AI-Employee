"""Stable view model for the role-aware Platform Command Center workspace."""

from __future__ import annotations

from typing import Any


def workspace_view(summary: dict[str, Any]) -> dict[str, Any]:
    """Expose only workspace-safe command-center fields."""
    overview = summary.get("overview", {})
    return {
        "total_work_items": overview.get("total_work_items", 0),
        "lifecycle": overview.get("lifecycle", {}),
        "executor_mix": overview.get("executor_mix", {}),
        "waiting_approval": overview.get("waiting_approval", 0),
        "failed": overview.get("failed", 0),
        "attention": summary.get("attention", []),
        "action_readiness": summary.get("action_readiness", []),
        "attention_count": summary.get("attention_count", 0),
        "actionable_count": summary.get("actionable_count", 0),
    }

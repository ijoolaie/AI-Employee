"""Deterministic, tenant-governed campaign planning for the AI Marketing Manager."""

from __future__ import annotations

from typing import Any


def draft_campaign_plan(
    *,
    tenant_id: str,
    objective: str,
    audience: str,
    channels: list[str],
    duration_days: int = 30,
    budget: float | None = None,
    offer: str | None = None,
) -> dict[str, Any]:
    """Create a structured campaign plan without executing or persisting anything.

    The tenant identifier is required by the execution boundary but is never
    exposed in the generated plan. This function is deliberately deterministic:
    it produces planning output only and cannot launch campaigns, spend money,
    contact external systems, or claim measured campaign performance.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if duration_days < 1 or duration_days > 365:
        raise ValueError("duration_days must be 1-365")
    if budget is not None and budget < 0:
        raise ValueError("budget must be non-negative")

    normalized_channels = [channel.strip().lower() for channel in channels if channel.strip()]
    if not normalized_channels:
        raise ValueError("at least one channel is required")

    phases = [
        {
            "name": "planning",
            "days": min(3, duration_days),
            "activities": ["define message", "prepare creative brief", "define success metrics"],
        },
        {
            "name": "launch",
            "days": min(4, max(duration_days - 3, 1)),
            "activities": ["publish approved assets", "activate approved channels", "verify tracking"],
        },
        {
            "name": "optimization",
            "days": max(duration_days - 7, 0),
            "activities": ["review measured results", "test approved variants", "reallocate within approved limits"],
        },
    ]

    metrics = {
        "primary": ["objective completion"],
        "secondary": ["reach", "engagement", "conversion rate"],
        "guardrails": ["spend vs approved budget", "negative feedback", "conversion quality"],
    }

    return {
        "objective": objective.strip(),
        "audience": audience.strip(),
        "channels": normalized_channels,
        "duration_days": duration_days,
        "budget": budget,
        "offer": offer.strip() if offer else None,
        "phases": phases,
        "metrics": metrics,
        "governance": {
            "execution_required": True,
            "external_spend_requires_approval": True,
            "campaign_attribution_requires_measured_data": True,
        },
        "status": "draft",
    }

"""Tenant-governed content coordination planning for the AI Marketing Manager."""

from __future__ import annotations

from typing import Any


_CHANNEL_DELIVERABLES = {
    "email": ("subject_line", "body_copy", "cta"),
    "social": ("primary_post", "short_variant", "cta"),
    "instagram": ("caption", "creative_brief", "cta"),
    "linkedin": ("professional_post", "proof_points", "cta"),
    "blog": ("outline", "key_points", "cta"),
    "website": ("landing_page_outline", "value_proposition", "cta"),
}


def coordinate_content(
    *,
    tenant_id: str,
    objective: str,
    channels: list[str],
    audience: str,
    key_message: str,
    offer: str | None = None,
) -> dict[str, Any]:
    """Create a channel-aware content work package without publishing anything."""
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not objective.strip() or not audience.strip() or not key_message.strip():
        raise ValueError("objective, audience, and key_message are required")

    normalized_channels = []
    for channel in channels:
        value = channel.strip().lower()
        if value and value not in normalized_channels:
            normalized_channels.append(value)
    if not normalized_channels:
        raise ValueError("at least one channel is required")

    deliverables = []
    unsupported = []
    for channel in normalized_channels:
        items = _CHANNEL_DELIVERABLES.get(channel)
        if items is None:
            unsupported.append(channel)
            items = ("primary_copy", "channel_variant", "cta")
        deliverables.append(
            {
                "channel": channel,
                "deliverables": list(items),
                "owner_role": "ai_graphic_designer"
                if channel in {"instagram", "social"}
                else "ai_marketing_advertising_manager",
                "status": "planned",
            }
        )

    return {
        "status": "planned",
        "objective": objective.strip(),
        "audience": audience.strip(),
        "key_message": key_message.strip(),
        "offer": offer.strip() if offer else None,
        "deliverables": deliverables,
        "unsupported_channel_notes": unsupported,
        "governance": {
            "publication_requires_separate_execution": True,
            "external_spend_requires_approval": True,
            "external_provider_access_not_performed": True,
        },
    }

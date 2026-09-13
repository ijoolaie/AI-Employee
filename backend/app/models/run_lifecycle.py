"""Run lifecycle transition guard helpers.

Centralizes allowed Run status transitions so execution boundaries cannot
silently mutate a Run into an invalid lifecycle state.
"""

from __future__ import annotations


ALLOWED_RUN_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "cancelled"},
    "running": {"success", "failed", "waiting", "cancelled"},
    "waiting": {"running", "failed", "cancelled"},
    "success": set(),
    "failed": set(),
    "cancelled": set(),
}


def can_transition(current: str, target: str) -> bool:
    if current == target:
        return True
    return target in ALLOWED_RUN_TRANSITIONS.get(current, set())


def validate_transition(current: str, target: str) -> None:
    if not can_transition(current, target):
        raise ValueError(
            f"Invalid Run lifecycle transition: {current} -> {target}"
        )

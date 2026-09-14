"""Durable workflow state transition rules.

Keeps workflow step lifecycle changes explicit so execution paths cannot
silently jump between incompatible states.
"""

from __future__ import annotations

from app.core.exceptions import ValidationAppError


STEP_STATES = {
    "pending",
    "running",
    "dispatched",
    "executing",
    "waiting",
    "waiting_parallel",
    "retry_wait",
    "success",
    "failed",
    "skipped",
    "cancelled",
}


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "dispatched", "cancelled"},
    "dispatched": {"executing", "failed", "cancelled"},
    "running": {"executing", "waiting", "waiting_parallel", "retry_wait", "success", "failed", "cancelled"},
    "executing": {"success", "retry_wait", "failed", "cancelled"},
    "waiting": {"running", "success", "failed", "cancelled"},
    "waiting_parallel": {"running", "success", "failed", "cancelled"},
    "retry_wait": {"running", "executing", "failed", "cancelled"},
    "success": set(),
    "failed": set(),
    "skipped": set(),
    "cancelled": set(),
}


def assert_step_transition(current: str, target: str) -> None:
    if current not in STEP_STATES:
        raise ValidationAppError(f"Unknown workflow step state: {current}")
    if target not in STEP_STATES:
        raise ValidationAppError(f"Unknown workflow step target state: {target}")
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValidationAppError(
            f"Invalid workflow step transition: {current} -> {target}"
        )


def transition_step(step, target: str) -> None:
    assert_step_transition(step.status, target)
    step.status = target

"""Deterministic, side-effect-free evaluation contract for Agent/Test Center runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


_FORBIDDEN_KEY_PARTS = (
    "prompt",
    "memory",
    "embedding",
    "secret",
    "token",
    "password",
    "authorization",
    "tool_args",
    "tool_arguments",
    "failure_detail",
    "stacktrace",
)


@dataclass(frozen=True)
class EvaluationResult:
    """Immutable evaluation evidence suitable for persistence/export."""

    passed: bool
    score: float
    reasons: tuple[str, ...]
    contract_version: str = "13.6.1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in _FORBIDDEN_KEY_PARTS):
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def evaluate_run(
    *,
    expected: dict[str, Any],
    result: dict[str, Any],
    evidence: dict[str, Any],
    run_status: str,
    approval_state: str = "not_required",
) -> EvaluationResult:
    """Evaluate a completed Test Center run without executing arbitrary code.

    Supported deterministic expectations:
    - ``equals``: exact JSON equality against the result payload.
    - ``required_keys``: keys that must exist in the result payload.
    - ``forbidden_keys``: keys that must not exist in the result payload.
    - ``approval_required``: requires the recorded approval state to be approved.
    - ``evidence_keys``: evidence fields that must be present.

    The evaluator never consumes prompts, memory text, embeddings, secrets, tool
    arguments, authorization material, or failure-detail payloads.
    """
    reasons: list[str] = []
    if run_status not in {"passed", "failed", "cancelled", "expired"}:
        reasons.append("evaluation requires a terminal run")

    if _contains_forbidden_key(result) or _contains_forbidden_key(evidence):
        reasons.append("evaluation payload contains a forbidden sensitive key")

    equals = expected.get("equals")
    if equals is not None and _canonical(result) != _canonical(equals):
        reasons.append("result does not match expected value")

    for key in expected.get("required_keys", []):
        if key not in result:
            reasons.append(f"missing required result key: {key}")

    for key in expected.get("forbidden_keys", []):
        if key in result:
            reasons.append(f"forbidden result key present: {key}")

    if expected.get("approval_required") is True and approval_state != "approved":
        reasons.append("required approval was not approved")

    for key in expected.get("evidence_keys", []):
        if key not in evidence:
            reasons.append(f"missing required evidence key: {key}")

    passed = not reasons
    return EvaluationResult(passed=passed, score=1.0 if passed else 0.0, reasons=tuple(reasons))

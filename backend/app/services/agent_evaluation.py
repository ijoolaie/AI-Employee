"""Deterministic, side-effect-free evaluation contract for Agent/Test Center runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


EVALUATION_CONTRACT_VERSION = "14.0.0"
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
    contract_version: str = EVALUATION_CONTRACT_VERSION


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


def _criterion_result(
    *,
    criterion: dict[str, Any],
    result: dict[str, Any],
    evidence: dict[str, Any],
    approval_state: str,
) -> tuple[bool, str]:
    kind = criterion.get("kind") or criterion.get("type")
    if kind == "equals":
        expected = criterion.get("value")
        passed = _canonical(result) == _canonical(expected)
        return passed, "equals criterion failed"
    if kind == "required_keys":
        keys = criterion.get("keys", [])
        missing = [key for key in keys if key not in result]
        return not missing, f"missing required result key: {missing[0]}" if missing else ""
    if kind == "forbidden_keys":
        keys = criterion.get("keys", [])
        present = [key for key in keys if key in result]
        return not present, f"forbidden result key present: {present[0]}" if present else ""
    if kind == "approval_required":
        passed = approval_state == "approved"
        return passed, "required approval was not approved"
    if kind == "evidence_keys":
        keys = criterion.get("keys", [])
        missing = [key for key in keys if key not in evidence]
        return not missing, f"missing required evidence key: {missing[0]}" if missing else ""
    return False, f"unsupported evaluation criterion: {kind}"


def evaluate_run(
    *,
    expected: dict[str, Any],
    result: dict[str, Any],
    evidence: dict[str, Any],
    run_status: str,
    approval_state: str = "not_required",
) -> EvaluationResult:
    """Evaluate a completed Test Center run without executing arbitrary code.

    Legacy expectations remain supported. New suites may use ``criteria`` with
    ``weight`` values and an optional ``threshold`` in [0, 1]. Every criterion
    must be deterministic and side-effect free.
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

    criteria = expected.get("criteria", [])
    if criteria:
        total_weight = 0.0
        weighted_score = 0.0
        for criterion in criteria:
            weight = float(criterion.get("weight", 1.0))
            if weight <= 0:
                reasons.append("evaluation criterion weight must be positive")
                continue
            passed, reason = _criterion_result(
                criterion=criterion,
                result=result,
                evidence=evidence,
                approval_state=approval_state,
            )
            total_weight += weight
            weighted_score += weight if passed else 0.0
            if not passed and reason:
                reasons.append(reason)
        score = weighted_score / total_weight if total_weight else 0.0
        threshold = float(expected.get("threshold", 1.0))
        if not 0.0 <= threshold <= 1.0:
            reasons.append("evaluation threshold must be between 0 and 1")
        elif score < threshold:
            reasons.append(f"evaluation score {score:.4f} is below threshold {threshold:.4f}")
    else:
        score = 1.0 if not reasons else 0.0

    passed = not reasons
    return EvaluationResult(passed=passed, score=score, reasons=tuple(reasons))

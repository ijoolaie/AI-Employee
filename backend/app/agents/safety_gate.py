"""Deterministic Phase 13.7 safety gate.

The gate verifies recorded safety properties around the existing Agent Runtime
contract. It never executes tools, model calls, arbitrary test code, or changes
run state. Its output is engineering evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agents.runtime_contract import AgentRuntimeContract


SENSITIVE_KEYS = frozenset(
    {
        "prompt",
        "memory",
        "embedding",
        "embeddings",
        "secret",
        "token",
        "authorization",
        "authorization_header",
        "tool_args",
        "tool_arguments",
        "failure_details",
        "stack_trace",
    }
)


@dataclass(frozen=True)
class SafetyGateEvidence:
    """Recorded outcomes of deterministic safety probes."""

    tenant_isolation: bool
    permission_enforcement: bool
    approval_enforcement: bool
    timeout_safety: bool
    retry_safety: bool
    evidence_integrity: bool
    negative_path_coverage: bool
    observed_tenant_ids: frozenset[str] = frozenset()
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class SafetyGateResult:
    """Stable, non-sensitive result of a Phase 13.7 gate evaluation."""

    passed: bool
    contract_version: str = "phase-13.7/v1"
    failed_checks: tuple[str, ...] = ()


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in SENSITIVE_KEYS:
                return True
            if _contains_sensitive_key(child):
                return True
    elif isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def evaluate_safety_gate(
    contract: AgentRuntimeContract,
    evidence: SafetyGateEvidence,
) -> SafetyGateResult:
    """Evaluate the Phase 13.7 gate without performing side effects.

    The function fails closed: invalid contracts, mismatched tenant evidence,
    explicit approval gaps, or sensitive evidence cause a failed gate.
    """

    failed: list[str] = []
    try:
        contract.validate()
    except ValueError:
        failed.append("runtime_contract")

    if evidence.observed_tenant_ids and evidence.observed_tenant_ids != frozenset(
        {contract.tenant_id}
    ):
        failed.append("tenant_isolation")
    elif not evidence.tenant_isolation:
        failed.append("tenant_isolation")

    if not evidence.permission_enforcement:
        failed.append("permission_enforcement")

    approval_required = contract.approval_state != "not_required"
    if approval_required and contract.approval_state != "granted":
        failed.append("approval_enforcement")
    elif not evidence.approval_enforcement:
        failed.append("approval_enforcement")

    if contract.timeout_seconds < 1 or not evidence.timeout_safety:
        failed.append("timeout_safety")

    if contract.retry.max_attempts < 1 or not evidence.retry_safety:
        failed.append("retry_safety")

    if not evidence.evidence_integrity:
        failed.append("evidence_integrity")
    if not evidence.negative_path_coverage:
        failed.append("negative_path_coverage")

    if _contains_sensitive_key(evidence.evidence or {}):
        failed.append("sensitive_evidence")

    # Runtime evidence is allowed to carry correlation identifiers only.
    if evidence.evidence:
        allowed = {
            "tenant_id",
            "run_id",
            "employee_id",
            "employee_version_id",
            "approval_id",
            "outcome",
            "attempts",
            "passed",
            "checks",
        }
        unexpected = set(evidence.evidence) - allowed
        if unexpected:
            failed.append("evidence_integrity")

    return SafetyGateResult(passed=not failed, failed_checks=tuple(dict.fromkeys(failed)))

"""Explicit contract for safe Agent Runtime execution.

Phase 13.1 defines the immutable inputs and lifecycle controls that every
future agent execution must carry: tenant/run identity, employee version,
input/context/memory, allowed tools, permissions, approval state, timeout,
retry policy, output, and evidence metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ApprovalState = Literal["not_required", "pending", "granted", "rejected"]


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    backoff_seconds: float = 0.0

    def validate(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("retry.max_attempts must be >= 1")
        if self.backoff_seconds < 0:
            raise ValueError("retry.backoff_seconds must be >= 0")


@dataclass
class AgentRuntimeContract:
    tenant_id: str
    run_id: str
    employee_id: str
    employee_version_id: str
    input_data: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    memory: list[dict[str, Any]] = field(default_factory=list)
    allowed_tools: frozenset[str] = field(default_factory=frozenset)
    permissions: frozenset[str] = field(default_factory=frozenset)
    approval_state: ApprovalState = "not_required"
    approval_id: str | None = None
    timeout_seconds: int = 300
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    output_data: dict[str, Any] | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        required_identity = {
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "employee_id": self.employee_id,
            "employee_version_id": self.employee_version_id,
        }
        missing = [name for name, value in required_identity.items() if not value]
        if missing:
            raise ValueError(f"runtime identity is incomplete: {', '.join(missing)}")
        if not isinstance(self.input_data, dict):
            raise ValueError("input_data must be an object")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")
        if self.approval_state in {"pending", "granted", "rejected"} and not self.approval_id:
            raise ValueError("approval_id is required for an explicit approval state")
        if self.approval_state == "not_required" and self.approval_id is not None:
            raise ValueError("approval_id must be absent when approval is not required")
        if any(not tool for tool in self.allowed_tools):
            raise ValueError("allowed_tools cannot contain empty names")
        if any(not permission for permission in self.permissions):
            raise ValueError("permissions cannot contain empty names")
        self.retry.validate()

    def evidence_context(self) -> dict[str, Any]:
        """Return only stable correlation fields for audit/observability."""
        return {
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "employee_id": self.employee_id,
            "employee_version_id": self.employee_version_id,
            "approval_id": self.approval_id,
        }

"""Tenant-safe Test Center execution contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


class TestCenterError(RuntimeError):
    """Raised when a test run violates safety or tenancy policy."""


@dataclass
class TestRun:
    tenant_id: UUID
    actor_id: UUID
    family: str
    safe_mode: bool = True
    mutation_requested: bool = False
    id: UUID = field(default_factory=uuid4)
    status: str = "pending"
    evidence: list[dict[str, Any]] = field(default_factory=list)


class TestCenterService:
    """Minimal backend contract for safe, role-aware test execution."""

    MUTATING_FAMILIES = {"workflow", "handoff", "tool", "billing"}

    def start(self, run: TestRun, *, actor_tenant_id: UUID) -> TestRun:
        if run.tenant_id != actor_tenant_id:
            raise TestCenterError("test run tenant mismatch")
        if run.safe_mode and run.mutation_requested:
            raise TestCenterError("safe mode forbids production mutation")
        run.status = "running"
        run.evidence.append({"event": "started", "family": run.family, "safe_mode": run.safe_mode})
        return run

    def complete(self, run: TestRun, *, passed: bool, evidence: dict[str, Any] | None = None) -> TestRun:
        if run.status != "running":
            raise TestCenterError("test run is not active")
        run.status = "passed" if passed else "failed"
        run.evidence.append({"event": run.status, **(evidence or {})})
        return run

    @staticmethod
    def export_evidence(run: TestRun) -> dict[str, Any]:
        return {
            "run_id": str(run.id),
            "tenant_id": str(run.tenant_id),
            "actor_id": str(run.actor_id),
            "family": run.family,
            "status": run.status,
            "safe_mode": run.safe_mode,
            "evidence": list(run.evidence),
        }

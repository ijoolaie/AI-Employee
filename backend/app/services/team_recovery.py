"""Recovery and completion gates for tenant-scoped Agent Team runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class RecoveryError(RuntimeError):
    """Raised when a TeamRun cannot safely recover or complete."""


class TeamRunStatus(str, Enum):
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class TeamRun:
    tenant_id: UUID
    correlation_id: str
    status: TeamRunStatus = TeamRunStatus.RUNNING
    required_members: set[str] = field(default_factory=set)
    completed_members: set[str] = field(default_factory=set)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def restore(self, *, tenant_id: UUID, snapshot: dict[str, Any]) -> "TeamRun":
        if tenant_id != self.tenant_id or snapshot.get("tenant_id") != str(self.tenant_id):
            raise RecoveryError("team run tenant mismatch")
        if snapshot.get("correlation_id") != self.correlation_id:
            raise RecoveryError("team run correlation mismatch")
        try:
            self.status = TeamRunStatus(snapshot["status"])
        except (KeyError, ValueError) as exc:
            raise RecoveryError("invalid team run status") from exc
        self.required_members = set(snapshot.get("required_members", []))
        self.completed_members = set(snapshot.get("completed_members", []))
        self.evidence = list(snapshot.get("evidence", []))
        return self

    def mark_member_complete(self, member_id: str) -> None:
        if self.status in {TeamRunStatus.FAILED, TeamRunStatus.COMPLETED}:
            raise RecoveryError("team run is terminal")
        self.completed_members.add(member_id)

    def can_complete(self) -> bool:
        return self.status == TeamRunStatus.RUNNING and self.required_members <= self.completed_members

    def complete(self) -> None:
        if not self.can_complete():
            raise RecoveryError("completion gates not satisfied")
        self.status = TeamRunStatus.COMPLETED
        self.evidence.append({"event": "completed", "correlation_id": self.correlation_id})

    def fail(self, reason: str) -> None:
        if self.status == TeamRunStatus.COMPLETED:
            raise RecoveryError("completed team run cannot fail")
        self.status = TeamRunStatus.FAILED
        self.evidence.append({"event": "failed", "reason": reason, "correlation_id": self.correlation_id})

    def checkpoint(self) -> dict[str, Any]:
        return {
            "run_id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "correlation_id": self.correlation_id,
            "status": self.status.value,
            "required_members": sorted(self.required_members),
            "completed_members": sorted(self.completed_members),
            "evidence": list(self.evidence),
        }

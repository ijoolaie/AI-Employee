"""Checkpoint and replay primitives for Agent Team runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.services.agent_teams import AgentTeamError, TeamRun, TeamRunStatus


@dataclass(frozen=True)
class TeamCheckpoint:
    tenant_id: UUID
    correlation_id: str
    status: TeamRunStatus
    approval_required: bool
    failure_reason: str | None
    evidence: tuple[dict[str, str], ...]


class TeamCheckpointStore:
    """Small durable-boundary abstraction; storage can be replaced by DB persistence."""

    def __init__(self) -> None:
        self._items: dict[tuple[UUID, str], TeamCheckpoint] = {}

    def save(self, run: TeamRun, *, actor_tenant_id: UUID) -> TeamCheckpoint:
        if actor_tenant_id != run.tenant_id:
            raise AgentTeamError("checkpoint tenant mismatch")
        key = (run.tenant_id, run.correlation_id)
        checkpoint = TeamCheckpoint(
            tenant_id=run.tenant_id,
            correlation_id=run.correlation_id,
            status=run.status,
            approval_required=run.approval_required,
            failure_reason=run.failure_reason,
            evidence=tuple(dict(item) for item in run.evidence),
        )
        self._items[key] = checkpoint
        return checkpoint

    def restore(self, *, tenant_id: UUID, correlation_id: str) -> TeamCheckpoint:
        checkpoint = self._items.get((tenant_id, correlation_id))
        if checkpoint is None:
            raise KeyError("checkpoint not found")
        return checkpoint

    def replay(self, run: TeamRun, *, actor_tenant_id: UUID) -> TeamRun:
        checkpoint = self.restore(tenant_id=actor_tenant_id, correlation_id=run.correlation_id)
        if run.tenant_id != checkpoint.tenant_id:
            raise AgentTeamError("replay tenant mismatch")
        run.status = checkpoint.status
        run.approval_required = checkpoint.approval_required
        run.failure_reason = checkpoint.failure_reason
        run.evidence = [dict(item) for item in checkpoint.evidence]
        return run

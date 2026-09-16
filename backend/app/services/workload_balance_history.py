"""Persistence boundary for Stage 9 workload balancing evidence."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workload_balance_event import WorkloadBalanceEvent
from app.services.workload_balancing import AgentLoadSnapshot, QueueSnapshot, WorkloadBalanceDecision


async def record_balance_decision(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    queue: QueueSnapshot,
    agents: list[AgentLoadSnapshot],
    decision: WorkloadBalanceDecision,
    target_agent_instance_id: uuid.UUID | None,
) -> WorkloadBalanceEvent:
    """Persist a recommendation snapshot without mutating execution state."""
    event = WorkloadBalanceEvent(
        tenant_id=tenant_id,
        target_agent_instance_id=target_agent_instance_id,
        ready_items=max(queue.ready_items, 0),
        oldest_ready_age_seconds=max(queue.oldest_ready_age_seconds, 0.0),
        total_available_slots=sum(agent.available_slots for agent in agents if agent.accepting_work),
        queue_pressure=max(decision.queue_pressure, 0.0),
        candidates_considered=max(decision.candidates_considered, 0),
        rationale=list(decision.rationale),
        contract_version=decision.contract_version,
    )
    db.add(event)
    await db.flush()
    return event


async def list_balance_history(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    limit: int = 50,
    target_agent_instance_id: uuid.UUID | None = None,
) -> list[WorkloadBalanceEvent]:
    """Return tenant-scoped recommendation history in newest-first order."""
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200")

    query = select(WorkloadBalanceEvent).where(WorkloadBalanceEvent.tenant_id == tenant_id)
    if target_agent_instance_id is not None:
        query = query.where(WorkloadBalanceEvent.target_agent_instance_id == target_agent_instance_id)
    query = query.order_by(WorkloadBalanceEvent.created_at.desc()).limit(limit)
    return list((await db.execute(query)).scalars().all())

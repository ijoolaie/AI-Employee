"""Governed workforce assignment and capacity management."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.agent_kill_switch_service import assert_not_killed
from app.services.unified_execution import ExecutionError


ACTIVE_WORK_ITEM_STATUSES = (WorkItemStatus.ASSIGNED, WorkItemStatus.RUNNING)


async def get_agent_capacity(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
    for_update: bool = False,
) -> dict[str, int | bool]:
    """Return tenant-scoped capacity without exposing cross-tenant workload."""
    stmt = select(AgentInstance).where(
        AgentInstance.id == agent_instance_id,
        AgentInstance.tenant_id == tenant_id,
    )
    if for_update:
        stmt = stmt.with_for_update()
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise ExecutionError("agent instance not found")

    active = await db.scalar(
        select(func.count(WorkItem.id)).where(
            WorkItem.tenant_id == tenant_id,
            WorkItem.executor_type == ExecutorType.AGENT,
            WorkItem.executor_id == agent_instance_id,
            WorkItem.status.in_(ACTIVE_WORK_ITEM_STATUSES),
        )
    )
    active_count = int(active or 0)
    limit = max(1, int(agent.max_concurrency))
    available = max(0, limit - active_count)
    return {
        "max_concurrency": limit,
        "active_work_items": active_count,
        "available_slots": available,
        "accepting_work": bool(
            agent.enabled
            and agent.status is AgentInstanceStatus.ENABLED
            and available > 0
        ),
    }


async def assign_work_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    work_item_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
) -> WorkItem:
    """Atomically assign a WorkItem while enforcing Agent concurrency and kill switches."""
    await assert_not_killed(
        db,
        tenant_id=tenant_id,
        agent_instance_id=agent_instance_id,
    )

    agent_stmt = (
        select(AgentInstance)
        .where(
            AgentInstance.id == agent_instance_id,
            AgentInstance.tenant_id == tenant_id,
        )
        .with_for_update()
    )
    agent = (await db.execute(agent_stmt)).scalar_one_or_none()
    if agent is None:
        raise ExecutionError("agent instance not found")
    if not agent.enabled or agent.status is not AgentInstanceStatus.ENABLED:
        raise ExecutionError("agent instance is not available")

    item_stmt = (
        select(WorkItem)
        .where(WorkItem.id == work_item_id, WorkItem.tenant_id == tenant_id)
        .with_for_update()
    )
    item = (await db.execute(item_stmt)).scalar_one_or_none()
    if item is None:
        raise ExecutionError("work item not found")
    if item.status in {WorkItemStatus.SUCCEEDED, WorkItemStatus.CANCELLED}:
        raise ExecutionError("terminal work items cannot be assigned")

    # A READY item may already carry the requested executor as an initial routing
    # hint. It still needs the ASSIGNED transition. Idempotency only applies once
    # the assignment state has actually been committed.
    if (
        item.status in ACTIVE_WORK_ITEM_STATUSES
        and item.executor_type is ExecutorType.AGENT
        and item.executor_id == agent_instance_id
    ):
        return item

    active = await db.scalar(
        select(func.count(WorkItem.id)).where(
            WorkItem.tenant_id == tenant_id,
            WorkItem.executor_type == ExecutorType.AGENT,
            WorkItem.executor_id == agent_instance_id,
            WorkItem.status.in_(ACTIVE_WORK_ITEM_STATUSES),
        )
    )
    active_count = int(active or 0)
    limit = max(1, int(agent.max_concurrency))
    if active_count >= limit:
        raise ExecutionError(
            f"agent concurrency limit reached ({active_count}/{limit})"
        )

    item.executor_type = ExecutorType.AGENT
    item.executor_id = agent.id
    item.status = WorkItemStatus.ASSIGNED
    await db.flush()
    return item

"""Read-only Stage 9 workforce capacity forecasting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import statistics
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.run import Run
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus

CAPACITY_FORECAST_CONTRACT_VERSION = "stage9-capacity-forecast-v1"


@dataclass(frozen=True)
class CapacityForecast:
    tenant_id: uuid.UUID
    window_days: int
    horizon_days: int
    sample_count: int
    demand_samples_per_day: float
    average_run_duration_seconds: float
    current_ready_items: int
    current_active_work_items: int
    total_max_concurrency: int
    total_available_slots: int
    projected_arrivals: float
    projected_required_concurrency: float
    projected_utilization: float
    projected_backlog: float
    lower_bound_required_concurrency: float
    upper_bound_required_concurrency: float
    evidence_complete: bool
    rationale: list[str]
    contract_version: str
    window_start: datetime
    window_end: datetime


async def capacity_forecast(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    window_days: int = 30,
    horizon_days: int = 7,
) -> CapacityForecast:
    """Estimate near-term workforce demand without changing workforce state.

    Demand is measured from tenant-scoped WorkItem creation volume. Service-time
    evidence comes from completed Agent Runs with both start and completion
    timestamps. Capacity is the current enabled Agent max-concurrency budget.
    Missing duration telemetry never becomes a zero-duration assumption.
    """
    if not 1 <= window_days <= 90:
        raise ValueError("window_days must be between 1 and 90")
    if not 1 <= horizon_days <= 30:
        raise ValueError("horizon_days must be between 1 and 30")

    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=window_days)

    demand_count = await db.scalar(
        select(func.count(WorkItem.id)).where(
            WorkItem.tenant_id == tenant_id,
            WorkItem.created_at >= window_start,
            WorkItem.created_at <= window_end,
            WorkItem.status != WorkItemStatus.CANCELLED,
        )
    )
    demand_samples = int(demand_count or 0)
    demand_per_day = demand_samples / float(window_days)

    completed_runs = list(
        (
            await db.execute(
                select(Run.started_at, Run.completed_at)
                .where(
                    Run.tenant_id == tenant_id,
                    Run.agent_instance_id.is_not(None),
                    Run.created_at >= window_start,
                    Run.created_at <= window_end,
                    Run.status == "success",
                    Run.started_at.is_not(None),
                    Run.completed_at.is_not(None),
                )
            )
        ).all()
    )
    durations = [
        max((completed - started).total_seconds(), 0.0)
        for started, completed in completed_runs
        if completed >= started
    ]
    average_duration = statistics.fmean(durations) if durations else 0.0

    ready_count = int(
        await db.scalar(
            select(func.count(WorkItem.id)).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.status == WorkItemStatus.READY,
            )
        )
        or 0
    )
    active_count = int(
        await db.scalar(
            select(func.count(WorkItem.id)).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.executor_type == ExecutorType.AGENT,
                WorkItem.status.in_([WorkItemStatus.ASSIGNED, WorkItemStatus.RUNNING]),
            )
        )
        or 0
    )

    agents = list(
        (
            await db.execute(
                select(AgentInstance).where(
                    AgentInstance.tenant_id == tenant_id,
                    AgentInstance.status == AgentInstanceStatus.ENABLED,
                    AgentInstance.enabled.is_(True),
                )
            )
        ).scalars().all()
    )
    total_capacity = sum(max(1, int(agent.max_concurrency)) for agent in agents)
    total_available = max(0, total_capacity - active_count)

    projected_arrivals = demand_per_day * horizon_days
    required_concurrency = demand_per_day * average_duration / 86400.0
    utilization = required_concurrency / total_capacity if total_capacity else 0.0
    projected_backlog = max(0.0, ready_count + projected_arrivals - max(total_capacity, 0) * horizon_days)

    # Bounds are deliberately descriptive rather than confidence intervals: the
    # observed daily arrival rate is represented by a conservative min/max band.
    lower_arrivals = max(0.0, demand_per_day * 0.5)
    upper_arrivals = demand_per_day * 1.5
    lower_required = lower_arrivals * average_duration / 86400.0
    upper_required = upper_arrivals * average_duration / 86400.0

    evidence_complete = bool(demand_samples > 0 and durations)
    rationale = [
        f"Observed {demand_samples} non-cancelled WorkItems over {window_days} days.",
        f"Observed {len(durations)} completed Agent Runs with duration telemetry.",
        f"Current enabled Agent concurrency capacity is {total_capacity} slots.",
    ]
    if not durations:
        rationale.append("Service-time evidence is unavailable; required concurrency is therefore zero rather than imputed.")
    if total_capacity == 0:
        rationale.append("No enabled Agent capacity is currently available.")
    if utilization > 1:
        rationale.append("Projected demand exceeds current maximum concurrency; this is evidence for review, not an automatic scaling command.")

    return CapacityForecast(
        tenant_id=tenant_id,
        window_days=window_days,
        horizon_days=horizon_days,
        sample_count=demand_samples,
        demand_samples_per_day=demand_per_day,
        average_run_duration_seconds=average_duration,
        current_ready_items=ready_count,
        current_active_work_items=active_count,
        total_max_concurrency=total_capacity,
        total_available_slots=total_available,
        projected_arrivals=projected_arrivals,
        projected_required_concurrency=required_concurrency,
        projected_utilization=utilization,
        projected_backlog=projected_backlog,
        lower_bound_required_concurrency=lower_required,
        upper_bound_required_concurrency=upper_required,
        evidence_complete=evidence_complete,
        rationale=rationale,
        contract_version=CAPACITY_FORECAST_CONTRACT_VERSION,
        window_start=window_start,
        window_end=window_end,
    )

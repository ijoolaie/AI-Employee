"""Stage 9 telemetry-backed Agent fitness.

Fitness is a read-only, tenant-scoped signal derived from durable execution
telemetry already recorded by the platform. It is deliberately separate from
Agent lifecycle and policy decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider_call import AIProviderCall
from app.models.feedback import Feedback
from app.models.run import Run


FITNESS_CONTRACT_VERSION = "agent-fitness-v1"


@dataclass(frozen=True)
class FitnessSample:
    """Durable telemetry for one Agent-associated Run."""

    run_id: uuid.UUID
    status: str
    latency_ms: float
    cost_usd: float
    feedback_rating: int | None = None


@dataclass(frozen=True)
class AgentFitness:
    """Explainable, bounded fitness signal for one Agent instance."""

    agent_instance_id: uuid.UUID
    sample_count: int
    success_rate: float
    feedback_score: float | None
    latency_score: float
    cost_score: float
    fitness: float
    window_start: datetime
    window_end: datetime
    contract_version: str = FITNESS_CONTRACT_VERSION


def _bounded(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def calculate_fitness(samples: Iterable[FitnessSample]) -> tuple[float, float, float, float, float | None]:
    """Return success, latency, cost, fitness and feedback scores.

    The components are normalized to [0, 1]. Missing feedback is excluded from
    the feedback average rather than treated as a negative signal.
    """
    items = list(samples)
    if not items:
        return 0.0, 0.0, 0.0, 0.0, None

    success_rate = sum(item.status == "success" for item in items) / len(items)
    ratings = [item.feedback_rating for item in items if item.feedback_rating is not None]
    feedback_score = (sum(ratings) / len(ratings) - 1.0) / 4.0 if ratings else None

    latencies = [max(item.latency_ms, 0.0) for item in items]
    positive_latencies = [value for value in latencies if value > 0]
    latency_score = 1.0 / (1.0 + (sum(positive_latencies) / len(positive_latencies)) / 1000.0) if positive_latencies else 1.0

    costs = [max(item.cost_usd, 0.0) for item in items]
    mean_cost = sum(costs) / len(costs)
    cost_score = 1.0 / (1.0 + mean_cost)

    components = [(success_rate, 0.45), (latency_score, 0.15), (cost_score, 0.15)]
    if feedback_score is not None:
        components.append((_bounded(feedback_score), 0.25))
        weight_total = 1.0
    else:
        weight_total = 0.75
    fitness = sum(score * weight for score, weight in components) / weight_total
    return (
        _bounded(success_rate),
        _bounded(latency_score),
        _bounded(cost_score),
        _bounded(fitness),
        None if feedback_score is None else _bounded(feedback_score),
    )


async def agent_fitness_summary(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID | None = None,
    window_days: int = 30,
) -> list[AgentFitness]:
    """Aggregate durable Run/provider-call/feedback telemetry by Agent.

    Only completed telemetry in the requested tenant/window is considered.
    No Agent, Run, budget, approval, or policy state is mutated.
    """
    if window_days < 1 or window_days > 90:
        raise ValueError("window_days must be between 1 and 90")

    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=window_days)

    run_query = select(Run).where(
        Run.tenant_id == tenant_id,
        Run.agent_instance_id.is_not(None),
        Run.created_at >= window_start,
        Run.created_at <= window_end,
        Run.status.in_(["success", "failed", "cancelled"]),
    )
    if agent_instance_id is not None:
        run_query = run_query.where(Run.agent_instance_id == agent_instance_id)
    runs = list((await db.execute(run_query)).scalars().all())
    if not runs:
        return []

    run_ids = [run.id for run in runs]
    call_rows = list(
        (await db.execute(
            select(AIProviderCall).where(
                AIProviderCall.tenant_id == tenant_id,
                AIProviderCall.run_id.in_(run_ids),
            )
        )).scalars().all()
    )
    feedback_rows = list(
        (await db.execute(
            select(Feedback).where(
                Feedback.tenant_id == tenant_id,
                Feedback.run_id.in_(run_ids),
                Feedback.category == "run",
            )
        )).scalars().all()
    )

    latency_by_run: dict[uuid.UUID, float] = {}
    for call in call_rows:
        latency_by_run[call.run_id] = latency_by_run.get(call.run_id, 0.0) + max(float(call.latency_ms or 0), 0.0)

    feedback_by_run: dict[uuid.UUID, int] = {}
    for feedback in feedback_rows:
        if feedback.run_id is not None:
            feedback_by_run[feedback.run_id] = feedback.rating

    grouped: dict[uuid.UUID, list[FitnessSample]] = {}
    for run in runs:
        if run.agent_instance_id is None:
            continue
        grouped.setdefault(run.agent_instance_id, []).append(
            FitnessSample(
                run_id=run.id,
                status=run.status,
                latency_ms=latency_by_run.get(run.id, 0.0),
                cost_usd=float(run.total_cost_usd or 0),
                feedback_rating=feedback_by_run.get(run.id),
            )
        )

    result: list[AgentFitness] = []
    for agent_id in sorted(grouped, key=str):
        samples = grouped[agent_id]
        success_rate, latency_score, cost_score, fitness, feedback_score = calculate_fitness(samples)
        result.append(
            AgentFitness(
                agent_instance_id=agent_id,
                sample_count=len(samples),
                success_rate=success_rate,
                feedback_score=feedback_score,
                latency_score=latency_score,
                cost_score=cost_score,
                fitness=fitness,
                window_start=window_start,
                window_end=window_end,
            )
        )
    return result

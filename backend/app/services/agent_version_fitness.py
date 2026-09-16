"""Stage 9 fitness aggregated by immutable AgentTemplate version."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_instance import AgentInstance
from app.models.agent_template import AgentTemplate
from app.models.ai_provider_call import AIProviderCall
from app.models.feedback import Feedback
from app.models.run import Run
from app.services.agent_fitness import FITNESS_CONTRACT_VERSION, FitnessSample, calculate_fitness


@dataclass(frozen=True)
class AgentVersionFitness:
    """Explainable, bounded fitness for one AgentTemplate version."""

    agent_template_id: uuid.UUID
    agent_instance_count: int
    slug: str
    version: int
    sample_count: int
    success_rate: float
    feedback_score: float | None
    latency_score: float
    cost_score: float
    fitness: float
    window_start: datetime
    window_end: datetime
    contract_version: str = FITNESS_CONTRACT_VERSION


async def agent_version_fitness_summary(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_template_id: uuid.UUID | None = None,
    window_days: int = 30,
) -> list[AgentVersionFitness]:
    """Aggregate durable execution telemetry by tenant-scoped AgentTemplate version.

    Version identity comes from the AgentInstance -> AgentTemplate binding. The
    operation is read-only and never changes Agent lifecycle, policy, approval,
    budget, assignment, or promotion state.
    """
    if window_days < 1 or window_days > 90:
        raise ValueError("window_days must be between 1 and 90")

    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=window_days)

    query = (
        select(Run, AgentInstance, AgentTemplate)
        .join(AgentInstance, AgentInstance.id == Run.agent_instance_id)
        .join(AgentTemplate, AgentTemplate.id == AgentInstance.agent_template_id)
        .where(
            Run.tenant_id == tenant_id,
            AgentInstance.tenant_id == tenant_id,
            AgentTemplate.tenant_id == tenant_id,
            Run.agent_instance_id.is_not(None),
            Run.created_at >= window_start,
            Run.created_at <= window_end,
            Run.status.in_(["success", "failed", "cancelled"]),
        )
    )
    if agent_template_id is not None:
        query = query.where(AgentTemplate.id == agent_template_id)

    rows = list((await db.execute(query)).all())
    if not rows:
        return []

    run_ids = [run.id for run, _, _ in rows]
    calls = list(
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
    for call in calls:
        latency_by_run[call.run_id] = latency_by_run.get(call.run_id, 0.0) + max(float(call.latency_ms or 0), 0.0)

    feedback_by_run: dict[uuid.UUID, int] = {}
    for feedback in feedback_rows:
        if feedback.run_id is not None:
            feedback_by_run[feedback.run_id] = feedback.rating

    grouped: dict[uuid.UUID, tuple[AgentTemplate, set[uuid.UUID], list[FitnessSample]]] = {}
    for run, instance, template in rows:
        bucket = grouped.setdefault(template.id, (template, set(), []))
        bucket[1].add(instance.id)
        bucket[2].append(
            FitnessSample(
                run_id=run.id,
                status=run.status,
                latency_ms=latency_by_run.get(run.id, 0.0),
                cost_usd=float(run.total_cost_usd or 0),
                feedback_rating=feedback_by_run.get(run.id),
            )
        )

    result: list[AgentVersionFitness] = []
    for template_id in sorted(grouped, key=str):
        template, instance_ids, samples = grouped[template_id]
        success_rate, latency_score, cost_score, fitness, feedback_score = calculate_fitness(samples)
        result.append(
            AgentVersionFitness(
                agent_template_id=template_id,
                agent_instance_count=len(instance_ids),
                slug=template.slug,
                version=template.version,
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

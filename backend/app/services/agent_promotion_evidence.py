"""Stage 9 read-only evidence for AgentTemplate version promotion."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_fitness import FITNESS_CONTRACT_VERSION
from app.services.agent_version_fitness import AgentVersionFitness, agent_version_fitness_summary


@dataclass(frozen=True)
class AgentPromotionEvidence:
    """Comparable telemetry evidence; it never authorizes lifecycle changes."""

    candidate_agent_template_id: UUID
    candidate_slug: str
    candidate_version: int
    candidate_sample_count: int
    candidate_fitness: float
    baseline_agent_template_id: UUID | None
    baseline_version: int | None
    baseline_sample_count: int
    baseline_fitness: float | None
    fitness_delta: float | None
    comparable: bool
    evidence_window_start: object
    evidence_window_end: object
    contract_version: str = FITNESS_CONTRACT_VERSION


def build_promotion_evidence(
    candidate: AgentVersionFitness,
    baseline: AgentVersionFitness | None,
) -> AgentPromotionEvidence:
    """Build a neutral candidate-vs-prior-version evidence snapshot."""
    comparable = (
        baseline is not None
        and baseline.slug == candidate.slug
        and baseline.version < candidate.version
        and baseline.sample_count > 0
        and candidate.sample_count > 0
    )
    delta = candidate.fitness - baseline.fitness if comparable and baseline is not None else None
    return AgentPromotionEvidence(
        candidate_agent_template_id=candidate.agent_template_id,
        candidate_slug=candidate.slug,
        candidate_version=candidate.version,
        candidate_sample_count=candidate.sample_count,
        candidate_fitness=candidate.fitness,
        baseline_agent_template_id=baseline.agent_template_id if comparable and baseline else None,
        baseline_version=baseline.version if comparable and baseline else None,
        baseline_sample_count=baseline.sample_count if comparable and baseline else 0,
        baseline_fitness=baseline.fitness if comparable and baseline else None,
        fitness_delta=delta,
        comparable=comparable,
        evidence_window_start=candidate.window_start,
        evidence_window_end=candidate.window_end,
    )


async def agent_promotion_evidence_summary(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    agent_template_id: UUID | None = None,
    window_days: int = 30,
) -> list[AgentPromotionEvidence]:
    """Compare each candidate version with the nearest prior measured version.

    This is evidence-only: no promotion, publication, retirement, assignment,
    approval, policy, budget, or lifecycle state is changed.
    """
    versions = await agent_version_fitness_summary(
        db,
        tenant_id=tenant_id,
        agent_template_id=None,
        window_days=window_days,
    )
    if agent_template_id is not None:
        versions = [item for item in versions if item.agent_template_id == agent_template_id]

    by_slug: dict[str, list[AgentVersionFitness]] = {}
    for item in versions:
        by_slug.setdefault(item.slug, []).append(item)

    result: list[AgentPromotionEvidence] = []
    for slug in sorted(by_slug):
        ordered = sorted(by_slug[slug], key=lambda item: (item.version, str(item.agent_template_id)))
        for candidate in ordered:
            prior = [item for item in ordered if item.version < candidate.version]
            baseline = prior[-1] if prior else None
            result.append(build_promotion_evidence(candidate, baseline))
    return result

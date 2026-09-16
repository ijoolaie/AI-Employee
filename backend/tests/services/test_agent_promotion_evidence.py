from datetime import datetime, timezone
import uuid

import pytest
from unittest.mock import AsyncMock

from app.services.agent_promotion_evidence import build_promotion_evidence, agent_promotion_evidence_summary
from app.services.agent_version_fitness import AgentVersionFitness


def _fitness(*, slug: str, version: int, value: float, samples: int = 10) -> AgentVersionFitness:
    now = datetime.now(timezone.utc)
    return AgentVersionFitness(
        agent_template_id=uuid.uuid4(),
        agent_instance_count=1,
        slug=slug,
        version=version,
        sample_count=samples,
        success_rate=value,
        feedback_score=None,
        latency_score=value,
        cost_score=value,
        fitness=value,
        window_start=now,
        window_end=now,
    )


def test_promotion_evidence_compares_candidate_with_nearest_prior_version():
    baseline = _fitness(slug="support", version=1, value=0.70)
    candidate = _fitness(slug="support", version=2, value=0.82)

    evidence = build_promotion_evidence(candidate, baseline)

    assert evidence.comparable is True
    assert evidence.baseline_version == 1
    assert evidence.fitness_delta == pytest.approx(0.12)


def test_promotion_evidence_is_not_comparable_without_prior_version():
    candidate = _fitness(slug="support", version=1, value=0.82)

    evidence = build_promotion_evidence(candidate, None)

    assert evidence.comparable is False
    assert evidence.baseline_version is None
    assert evidence.fitness_delta is None


@pytest.mark.asyncio
async def test_promotion_evidence_rejects_unbounded_window_before_database_access():
    db = AsyncMock()
    with pytest.raises(ValueError, match="window_days must be between 1 and 90"):
        await agent_promotion_evidence_summary(db, tenant_id=uuid.uuid4(), window_days=91)
    db.execute.assert_not_awaited()


def test_promotion_evidence_has_no_lifecycle_command():
    candidate = _fitness(slug="support", version=2, value=0.82)
    evidence = build_promotion_evidence(candidate, None)

    assert not hasattr(evidence, "promote")
    assert not hasattr(evidence, "publish")
    assert not hasattr(evidence, "retire")

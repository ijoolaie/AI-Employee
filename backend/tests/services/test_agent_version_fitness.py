from datetime import datetime, timezone
from unittest.mock import AsyncMock
import uuid

import pytest

from app.services.agent_fitness import FitnessSample, calculate_fitness
from app.services.agent_version_fitness import agent_version_fitness_summary


def test_version_fitness_reuses_bounded_scoring_contract():
    samples = [
        FitnessSample(uuid.uuid4(), "success", 100, 0.01, 5),
        FitnessSample(uuid.uuid4(), "failed", 300, 0.03, 3),
    ]
    _, _, _, fitness, feedback = calculate_fitness(samples)
    assert 0.0 <= fitness <= 1.0
    assert feedback == 0.5


@pytest.mark.asyncio
async def test_version_fitness_rejects_unbounded_window_before_database_access():
    db = AsyncMock()
    with pytest.raises(ValueError, match="window_days must be between 1 and 90"):
        await agent_version_fitness_summary(db, tenant_id=uuid.uuid4(), window_days=91)
    db.execute.assert_not_awaited()


def test_version_fitness_contract_is_read_only_by_design():
    """The public result is a measurement, not a promotion or lifecycle command."""
    from app.services.agent_version_fitness import AgentVersionFitness

    result = AgentVersionFitness(
        agent_template_id=uuid.uuid4(),
        agent_instance_count=1,
        slug="support",
        version=2,
        sample_count=3,
        success_rate=1.0,
        feedback_score=None,
        latency_score=0.9,
        cost_score=0.99,
        fitness=0.97,
        window_start=datetime.now(timezone.utc),
        window_end=datetime.now(timezone.utc),
    )
    assert result.fitness <= 1.0
    assert not hasattr(result, "promote")

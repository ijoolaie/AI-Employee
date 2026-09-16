from datetime import datetime, timezone
import uuid

import pytest

from app.services.agent_fitness import FitnessSample, calculate_fitness


def sample(*, status="success", latency_ms=500, cost_usd=0.1, rating=None):
    return FitnessSample(
        run_id=uuid.uuid4(),
        status=status,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        feedback_rating=rating,
    )


def test_fitness_is_bounded_and_uses_feedback():
    result = calculate_fitness([
        sample(rating=5),
        sample(rating=4),
        sample(status="error", latency_ms=1500, cost_usd=0.5),
    ])

    success_rate, latency_score, cost_score, fitness, feedback_score = result
    assert 0 <= success_rate <= 1
    assert 0 < latency_score <= 1
    assert 0 < cost_score <= 1
    assert 0 <= fitness <= 1
    assert feedback_score == pytest.approx(0.875)


def test_missing_feedback_is_not_penalized_as_a_zero_rating():
    with_feedback = calculate_fitness([sample(rating=5)])[3]
    without_feedback = calculate_fitness([sample()])[3]

    assert with_feedback > without_feedback
    assert 0 <= without_feedback <= 1


def test_empty_samples_fail_closed_to_zero_signal():
    assert calculate_fitness([]) == (0.0, 0.0, 0.0, 0.0, None)

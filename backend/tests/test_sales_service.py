"""Phase 9 — Sales Employee unit tests."""

from app.services.sales_service import ALLOWED_STAGES, DEFAULT_PROBABILITY


def test_stages():
    assert "lead" in ALLOWED_STAGES
    assert "won" in ALLOWED_STAGES
    assert "lost" in ALLOWED_STAGES


def test_default_probabilities():
    assert DEFAULT_PROBABILITY["lead"] == 10
    assert DEFAULT_PROBABILITY["won"] == 100
    assert DEFAULT_PROBABILITY["lost"] == 0
    assert DEFAULT_PROBABILITY["negotiation"] == 70

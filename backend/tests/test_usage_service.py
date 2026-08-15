"""Focused tests for usage aggregation edge-case helpers/contracts."""

from app.schemas.usage import UsageSummaryResponse


def test_usage_summary_contract_accepts_empty_report():
    result = UsageSummaryResponse.model_validate(
        {
            "from_at": None,
            "to_at": None,
            "calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0,
            "avg_latency_ms": 0,
            "breakdown": [],
            "notes": [],
        }
    )
    assert result.total_tokens == 0
    assert result.breakdown == []

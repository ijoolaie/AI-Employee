from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import usage as usage_api


@pytest.mark.asyncio
async def test_usage_optimization_uses_validated_portal_tenant(monkeypatch):
    tenant_id = uuid4()
    calls = []

    async def tenant_summary(_db, *, tenant_id):
        calls.append(tenant_id)
        return {
            "period_start": datetime(2026, 11, 1, tzinfo=timezone.utc),
            "plan": "business",
            "usage": {"runs": 2, "tokens": 30},
            "cost_usd": 0.12,
            "successful_work_items": 2,
            "cost_per_successful_work_item_usd": 0.06,
            "budget": {
                "state": "ok",
                "run_utilization": 0.1,
                "token_utilization": 0.2,
                "remaining_runs": 18,
                "remaining_tokens": 970,
            },
            "optimization_actions": [],
        }

    monkeypatch.setattr(usage_api.optimization_service, "tenant_optimization_summary", tenant_summary)
    response = await usage_api.get_usage_optimization(
        SimpleNamespace(tenant_id=tenant_id), object()
    )

    assert response.success is True
    assert response.data.plan == "business"
    assert calls == [tenant_id]


@pytest.mark.asyncio
async def test_usage_cost_forecast_uses_validated_portal_tenant(monkeypatch):
    tenant_id = uuid4()
    calls = []

    async def tenant_forecast(_db, *, tenant_id):
        calls.append(tenant_id)
        return {
            "as_of": datetime(2026, 11, 12, tzinfo=timezone.utc),
            "current_daily_cost_usd": 0.02,
            "baseline_daily_cost_usd": 0.01,
            "anomaly": False,
            "anomaly_score": 1.0,
            "month_to_date_cost_usd": 0.12,
            "projected_month_cost_usd": 0.31,
            "baseline_days": 7,
            "actions": ["Continue observing spend."],
        }

    monkeypatch.setattr(usage_api.cost_anomaly_service, "tenant_cost_anomaly_forecast", tenant_forecast)
    response = await usage_api.get_cost_forecast(
        SimpleNamespace(tenant_id=tenant_id), object()
    )

    assert response.success is True
    assert response.data.baseline_days == 7
    assert calls == [tenant_id]

"""Deterministic tenant cost anomaly detection and month-end forecasting."""
from __future__ import annotations

import calendar
import math
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider_call import AIProviderCall


def _daily_costs(rows: list[tuple[object, object]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for day, cost in rows:
        if day is None:
            continue
        key = day.isoformat() if hasattr(day, "isoformat") else str(day)
        result[key] = float(cost or 0)
    return result


def _anomaly(current: float, baseline: list[float]) -> tuple[bool, float]:
    if not baseline:
        return False, 0.0
    mean = sum(baseline) / len(baseline)
    variance = sum((value - mean) ** 2 for value in baseline) / len(baseline)
    stddev = math.sqrt(variance)
    if mean <= 0:
        return current > 0, 0.0 if current <= 0 else 1.0
    if stddev == 0:
        return current > mean * 1.5, round(current / mean, 4)
    z_score = (current - mean) / stddev
    return z_score >= 2.0, round(z_score, 4)


async def tenant_cost_anomaly_forecast(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    now: datetime | None = None,
) -> dict[str, object]:
    """Return a small, auditable cost signal using recorded provider-call costs only."""
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=14)
    rows = (
        await db.execute(
            select(func.date(AIProviderCall.created_at), func.coalesce(func.sum(AIProviderCall.cost_usd), 0))
            .where(AIProviderCall.tenant_id == tenant_id, AIProviderCall.created_at >= start)
            .group_by(func.date(AIProviderCall.created_at))
            .order_by(func.date(AIProviderCall.created_at))
        )
    ).all()
    costs = _daily_costs(rows)

    current_day = now.date()
    current = costs.get(current_day.isoformat(), 0.0)
    baseline = [costs.get((current_day - timedelta(days=offset)).isoformat(), 0.0) for offset in range(1, 8)]
    baseline_mean = sum(baseline) / len(baseline) if baseline else 0.0
    anomalous, score = _anomaly(current, baseline)

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_cost = sum(value for day, value in costs.items() if day >= month_start.date().isoformat())
    days_elapsed = max(1, now.day)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    projected = month_cost / days_elapsed * days_in_month

    actions: list[str] = []
    if anomalous:
        actions.append("Review today's provider usage, prompt/token intensity and recent workload changes.")
    if projected > 0 and month_cost > 0 and projected >= month_cost * 1.25:
        actions.append("Month-end spend is trending above current month-to-date spend; review budget headroom.")
    if not actions:
        actions.append("No material cost anomaly detected; continue observing daily spend and month-end forecast.")

    return {
        "as_of": now,
        "current_daily_cost_usd": round(current, 6),
        "baseline_daily_cost_usd": round(baseline_mean, 6),
        "anomaly": anomalous,
        "anomaly_score": score,
        "month_to_date_cost_usd": round(month_cost, 6),
        "projected_month_cost_usd": round(projected, 6),
        "baseline_days": len(baseline),
        "actions": actions,
    }

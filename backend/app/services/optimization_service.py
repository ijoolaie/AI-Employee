"""Phase 14.15 capacity, cost and operational optimization helpers.

The service deliberately builds on existing tenant-scoped billing and AI-call
records. It does not invent production capacity numbers: sizing is expressed
as a recommendation from measured throughput and an explicit utilization
headroom target.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider_call import AIProviderCall
from app.models.run import Run
from app.services import billing_service


def recommend_worker_count(
    *,
    observed_items_per_minute: float,
    target_items_per_minute: float,
    utilization_target: float = 0.70,
) -> int:
    """Return workers required for a target throughput with explicit headroom."""
    if observed_items_per_minute <= 0 or target_items_per_minute <= 0:
        raise ValueError("throughput values must be positive")
    if not 0 < utilization_target <= 1:
        raise ValueError("utilization_target must be in (0, 1]")
    effective_per_worker = observed_items_per_minute * utilization_target
    return max(1, math.ceil(target_items_per_minute / effective_per_worker))


def cost_per_work_item(*, total_cost_usd: Decimal | float, work_items: int) -> float:
    """Calculate cost per completed/created WorkItem without dividing by zero."""
    if work_items < 0:
        raise ValueError("work_items must be non-negative")
    if work_items == 0:
        return 0.0
    return float(Decimal(str(total_cost_usd)) / Decimal(work_items))


def budget_status(*, used_runs: int, run_limit: int, used_tokens: int, token_limit: int) -> dict[str, object]:
    """Return deterministic budget state used by operators and dashboards."""
    if run_limit <= 0 or token_limit <= 0:
        raise ValueError("budget limits must be positive")
    run_ratio = used_runs / run_limit
    token_ratio = used_tokens / token_limit
    ratio = max(run_ratio, token_ratio)
    state = "ok" if ratio < 0.80 else "warning" if ratio < 1.0 else "exhausted"
    return {
        "state": state,
        "run_utilization": round(run_ratio, 4),
        "token_utilization": round(token_ratio, 4),
        "remaining_runs": max(0, run_limit - used_runs),
        "remaining_tokens": max(0, token_limit - used_tokens),
    }


async def tenant_optimization_summary(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    now: datetime | None = None,
) -> dict[str, object]:
    """Aggregate monthly usage, unit economics and plan budget state."""
    now = now or datetime.now(timezone.utc)
    subscription = await billing_service.get_subscription(db, tenant_id=tenant_id)
    usage = await billing_service.monthly_usage(db, tenant_id=tenant_id, now=now)

    cost = (
        await db.execute(
            select(func.coalesce(func.sum(AIProviderCall.cost_usd), 0)).where(
                AIProviderCall.tenant_id == tenant_id,
                AIProviderCall.created_at >= billing_service._period_start(now),
            )
        )
    ).scalar_one()
    completed_runs = (
        await db.execute(
            select(func.count(Run.id)).where(
                Run.tenant_id == tenant_id,
                Run.created_at >= billing_service._period_start(now),
                Run.status == "success",
            )
        )
    ).scalar_one()
    avg_cost = cost_per_work_item(total_cost_usd=cost or 0, work_items=int(completed_runs or 0))

    return {
        "period_start": billing_service._period_start(now),
        "plan": subscription.plan.code,
        "usage": usage,
        "cost_usd": float(cost or 0),
        "successful_work_items": int(completed_runs or 0),
        "cost_per_successful_work_item_usd": avg_cost,
        "budget": budget_status(
            used_runs=usage["runs"],
            run_limit=subscription.plan.monthly_runs,
            used_tokens=usage["tokens"],
            token_limit=subscription.plan.monthly_tokens,
        ),
        "optimization_actions": _optimization_actions(
            usage=usage,
            budget=budget_status(
                used_runs=usage["runs"],
                run_limit=subscription.plan.monthly_runs,
                used_tokens=usage["tokens"],
                token_limit=subscription.plan.monthly_tokens,
            ),
        ),
    }


def _optimization_actions(*, usage: dict[str, int], budget: dict[str, object]) -> list[str]:
    actions: list[str] = []
    if budget["state"] == "exhausted":
        actions.append("Pause new work or move the tenant to a higher-capacity plan before the next burst.")
    elif budget["state"] == "warning":
        actions.append("Review token/run growth and queue backlog before increasing worker concurrency.")
    if usage["employees"] >= 1 and usage["runs"] == 0:
        actions.append("Review idle employee/workflow configuration; no monthly work has completed yet.")
    if usage["runs"] > 0 and usage["tokens"] / max(usage["runs"], 1) > 100_000:
        actions.append("Inspect prompt/context size and model selection; token intensity is unusually high.")
    if not actions:
        actions.append("No immediate optimization action; continue observing throughput, unit cost and budget utilization.")
    return actions

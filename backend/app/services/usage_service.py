"""Tenant-scoped usage and cost aggregation.

This is a read-only reporting layer over the durable AI Provider Call records.
It intentionally introduces no new storage or billing semantics: provider
calls remain the source of truth for model usage, latency and provider cost.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider_call import AIProviderCall


async def get_usage_summary(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
) -> dict[str, Any]:
    filters = [AIProviderCall.tenant_id == tenant_id]
    if from_at is not None:
        filters.append(AIProviderCall.created_at >= from_at)
    if to_at is not None:
        filters.append(AIProviderCall.created_at <= to_at)

    summary_result = await db.execute(
        select(
            func.count(AIProviderCall.id),
            func.sum(AIProviderCall.prompt_tokens),
            func.sum(AIProviderCall.completion_tokens),
            func.sum(AIProviderCall.cost_usd),
            func.avg(AIProviderCall.latency_ms),
        ).where(*filters)
    )
    calls, prompt_tokens, completion_tokens, cost_usd, avg_latency = summary_result.one()

    status_result = await db.execute(
        select(
            func.count(AIProviderCall.id),
            func.sum(case((AIProviderCall.status == "success", 1), else_=0)),
        ).where(*filters)
    )
    total_calls, successful_calls = status_result.one()
    total_calls = int(total_calls or 0)
    successful_calls = int(successful_calls or 0)

    breakdown_result = await db.execute(
        select(
            AIProviderCall.provider,
            AIProviderCall.model,
            func.count(AIProviderCall.id),
            func.sum(case((AIProviderCall.status == "success", 1), else_=0)),
            func.sum(AIProviderCall.prompt_tokens),
            func.sum(AIProviderCall.completion_tokens),
            func.sum(AIProviderCall.cost_usd),
            func.avg(AIProviderCall.latency_ms),
        )
        .where(*filters)
        .group_by(AIProviderCall.provider, AIProviderCall.model)
        .order_by(AIProviderCall.provider, AIProviderCall.model)
    )

    breakdown: list[dict[str, Any]] = []
    for provider, model, group_calls, group_success, group_prompt, group_completion, group_cost, group_latency in breakdown_result.all():
        group_calls = int(group_calls or 0)
        group_success = int(group_success or 0)
        group_prompt = int(group_prompt or 0)
        group_completion = int(group_completion or 0)
        breakdown.append(
            {
                "provider": provider,
                "model": model,
                "calls": group_calls,
                "successful_calls": group_success,
                "failed_calls": group_calls - group_success,
                "prompt_tokens": group_prompt,
                "completion_tokens": group_completion,
                "total_tokens": group_prompt + group_completion,
                "cost_usd": float(group_cost or 0),
                "avg_latency_ms": float(group_latency or 0),
            }
        )

    # Keep the aggregate query above as the authoritative call count.
    total_calls = total_calls or int(calls or 0)
    failed_calls = total_calls - successful_calls

    return {
        "from_at": from_at,
        "to_at": to_at,
        "calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "total_tokens": int(prompt_tokens or 0) + int(completion_tokens or 0),
        "cost_usd": float(cost_usd or 0),
        "avg_latency_ms": float(avg_latency or 0),
        "breakdown": breakdown,
        "notes": [
            "Cost is the provider-reported/accounting value recorded by AIGateway.",
            "Local LM Studio calls currently have zero provider API cost.",
            "Phase 4 quota enforcement is applied from the tenant subscription plan; invoices remain provider-adapter data.",
        ],
    }

"""Tenant-scoped usage reporting and idempotent usage ledger operations."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select


class UsageLimitExceeded(Exception):
    """Raised before an operation would exceed a tenant usage budget."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider_call import AIProviderCall
from app.models.usage import UsageEvent


async def record_event(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    event_key: str,
    category: str,
    quantity: int = 1,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float | Decimal = 0,
    source_type: str,
    source_id: str | None = None,
    metadata: dict | None = None,
) -> UsageEvent:
    """Record a usage event exactly once per tenant/event key.

    The database unique constraint is the final concurrency guard. A savepoint
    lets a concurrent duplicate insert fail without invalidating the caller's
    outer transaction; the winner's row is then returned.
    """
    existing = (
        await db.execute(
            select(UsageEvent).where(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.event_key == event_key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    event = UsageEvent(
        tenant_id=tenant_id,
        event_key=event_key,
        category=category,
        quantity=quantity,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
        source_type=source_type,
        source_id=source_id,
        event_metadata=metadata or {},
    )

    try:
        async with db.begin_nested():
            db.add(event)
            await db.flush()
    except IntegrityError:
        existing = (
            await db.execute(
                select(UsageEvent).where(
                    UsageEvent.tenant_id == tenant_id,
                    UsageEvent.event_key == event_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        raise

    return event


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


async def enforce_cost_limit(db: AsyncSession, *, tenant_id: uuid.UUID, max_cost_usd: float | Decimal, requested_cost_usd: float | Decimal = 0) -> None:
    """Fail closed when tenant cost plus a requested reservation exceeds a limit."""
    limit = Decimal(str(max_cost_usd))
    requested = Decimal(str(requested_cost_usd))
    if limit < 0 or requested < 0:
        raise ValueError("usage limits and requested cost must be non-negative")
    current = (await db.execute(select(func.coalesce(func.sum(UsageEvent.cost_usd), 0)).where(UsageEvent.tenant_id == tenant_id))).scalar_one()
    if Decimal(str(current)) + requested > limit:
        raise UsageLimitExceeded("tenant usage cost limit exceeded")

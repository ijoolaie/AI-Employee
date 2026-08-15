"""Run trace aggregation.

The first Trace layer is intentionally read-only and derives its timeline from
existing durable records: Run, AIProviderCall, and AuditLog. No new storage
or migration is required. This keeps trace data complete-by-construction while
leaving room for future tool/workflow spans.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.ai_provider_call import AIProviderCall
from app.models.audit_log import AuditLog
from app.models.run import Run


async def get_run_trace(
    db: AsyncSession, *, run_id: uuid.UUID, tenant_id: uuid.UUID
) -> dict[str, Any]:
    run_result = await db.execute(
        select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id)
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Run not found")

    calls_result = await db.execute(
        select(AIProviderCall)
        .where(
            AIProviderCall.run_id == run_id,
            AIProviderCall.tenant_id == tenant_id,
        )
        .order_by(AIProviderCall.created_at.asc())
    )
    calls = list(calls_result.scalars().all())

    audit_result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.resource_type == "run",
            AuditLog.resource_id == str(run_id),
        )
        .order_by(AuditLog.created_at.asc())
    )
    audits = list(audit_result.scalars().all())

    events: list[dict[str, Any]] = []
    for item in audits:
        events.append(
            {
                "type": "audit",
                "timestamp": item.created_at,
                "action": item.action,
                "status": item.status,
                "request_id": item.request_id,
                "metadata": item.metadata_,
            }
        )

    for call in calls:
        events.append(
            {
                "type": "ai_provider_call",
                "timestamp": call.created_at,
                "provider": call.provider,
                "model": call.model,
                "status": call.status,
                "prompt_tokens": call.prompt_tokens,
                "completion_tokens": call.completion_tokens,
                "cost_usd": float(call.cost_usd),
                "latency_ms": call.latency_ms,
                "prompt_version": call.prompt_version,
                "request_id": call.request_id,
                "metadata": call.raw_meta or {},
                "error_message": call.error_message,
            }
        )

    events.sort(key=lambda event: event["timestamp"])

    return {
        "run_id": run.id,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "total_tokens": run.total_tokens,
        "total_cost_usd": float(run.total_cost_usd),
        "events": events,
    }

"""Phase 1 operational metrics and dead-letter inspection helpers."""
from __future__ import annotations
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outbox import OutboxMessage
from app.models.workflow import WorkflowRun, WorkflowStepRun
from app.models.ai_provider_call import AIProviderCall

async def metrics_snapshot(db: AsyncSession, *, tenant_id: UUID | None = None) -> dict:
    def scoped(q):
        return q.where(OutboxMessage.tenant_id == tenant_id) if tenant_id else q
    q = scoped(select(func.count()).select_from(OutboxMessage).where(OutboxMessage.status == "pending"))
    pending = (await db.execute(q)).scalar_one()
    q = scoped(select(func.count()).select_from(OutboxMessage).where(OutboxMessage.status == "processing"))
    processing = (await db.execute(q)).scalar_one()
    q = scoped(select(func.count()).select_from(OutboxMessage).where(OutboxMessage.status == "dead"))
    dead = (await db.execute(q)).scalar_one()
    if tenant_id:
        runs = (await db.execute(select(func.count()).select_from(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id))).scalar_one()
        steps = (await db.execute(select(func.count()).select_from(WorkflowStepRun).join(WorkflowRun, WorkflowStepRun.workflow_run_id == WorkflowRun.id).where(WorkflowRun.tenant_id == tenant_id))).scalar_one()
        ai_calls = (await db.execute(select(func.count()).select_from(AIProviderCall).where(AIProviderCall.tenant_id == tenant_id))).scalar_one()
        ai_cost = (await db.execute(select(func.coalesce(func.sum(AIProviderCall.cost_usd), 0)).where(AIProviderCall.tenant_id == tenant_id))).scalar_one()
        ai_tokens = (await db.execute(select(func.coalesce(func.sum(AIProviderCall.prompt_tokens + AIProviderCall.completion_tokens), 0)).where(AIProviderCall.tenant_id == tenant_id))).scalar_one()
    else:
        runs = (await db.execute(select(func.count()).select_from(WorkflowRun))).scalar_one()
        steps = (await db.execute(select(func.count()).select_from(WorkflowStepRun))).scalar_one()
        ai_calls = (await db.execute(select(func.count()).select_from(AIProviderCall))).scalar_one()
        ai_cost = (await db.execute(select(func.coalesce(func.sum(AIProviderCall.cost_usd), 0)).select_from(AIProviderCall))).scalar_one()
        ai_tokens = (await db.execute(select(func.coalesce(func.sum(AIProviderCall.prompt_tokens + AIProviderCall.completion_tokens), 0)).select_from(AIProviderCall))).scalar_one()
    return {"outbox": {"pending": pending, "processing": processing, "dead": dead}, "workflow_runs_total": runs, "workflow_steps_total": steps, "ai": {"calls": ai_calls, "tokens": int(ai_tokens or 0), "cost_usd": float(ai_cost or 0)}}

async def list_dead_letters(db: AsyncSession, *, tenant_id: UUID, limit: int = 100) -> list[OutboxMessage]:
    result = await db.execute(select(OutboxMessage).where(OutboxMessage.tenant_id == tenant_id, OutboxMessage.status == "dead").order_by(OutboxMessage.dead_at.desc()).limit(min(max(limit,1),500)))
    return list(result.scalars().all())

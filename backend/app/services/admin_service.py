from __future__ import annotations

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import httpx
from redis.asyncio import Redis
from celery import Celery
from app.core.config import get_settings

from app.models.ai_provider_call import AIProviderCall
from app.models.outbox import OutboxMessage
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun


async def _health() -> dict:
    settings = get_settings()
    database = "healthy"
    redis_status = "unhealthy"
    celery_status = "unhealthy"
    provider_status = "unconfigured"

    try:
        redis = Redis.from_url(settings.redis_url, socket_connect_timeout=1.0, socket_timeout=1.0)
        await redis.ping()
        await redis.aclose()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    try:
        celery_app = Celery("admin-health", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
        inspect = celery_app.control.inspect(timeout=1.0)
        replies = await asyncio.to_thread(inspect.ping)
        celery_status = "healthy" if replies else "unhealthy"
    except Exception:
        celery_status = "unhealthy"

    if settings.ai_default_provider:
        provider_status = "configured"
        if settings.ai_default_provider.lower() in {"lm_studio", "lmstudio", "local"}:
            try:
                async with httpx.AsyncClient(timeout=1.5) as client:
                    response = await client.get(settings.lm_studio_base_url.rstrip("/") + "/models")
                    provider_status = "healthy" if response.status_code < 500 else "unhealthy"
            except Exception:
                provider_status = "unreachable"
    return {"database": database, "redis": redis_status, "celery": celery_status, "ai_provider": provider_status}


async def dashboard(db: AsyncSession) -> dict:
    tenants = (await db.execute(select(func.count()).select_from(Tenant))).scalar_one()
    active_tenants = (await db.execute(select(func.count()).select_from(Tenant).where(Tenant.status == "active"))).scalar_one()
    users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    workflows = (await db.execute(select(func.count()).select_from(Workflow))).scalar_one()
    workflow_runs = (await db.execute(select(func.count()).select_from(WorkflowRun))).scalar_one()
    failed_runs = (await db.execute(select(func.count()).select_from(WorkflowRun).where(WorkflowRun.status == "failed"))).scalar_one()
    ai_calls = (await db.execute(select(func.count()).select_from(AIProviderCall))).scalar_one()
    total_tokens = (await db.execute(select(func.coalesce(func.sum(AIProviderCall.prompt_tokens + AIProviderCall.completion_tokens), 0)))).scalar_one()
    total_cost = (await db.execute(select(func.coalesce(func.sum(AIProviderCall.cost_usd), 0)))).scalar_one()
    pending_outbox = (await db.execute(select(func.count()).select_from(OutboxMessage).where(OutboxMessage.status == "pending"))).scalar_one()
    dead_outbox = (await db.execute(select(func.count()).select_from(OutboxMessage).where(OutboxMessage.status == "dead"))).scalar_one()

    user_count_sq = select(func.count(User.id)).where(User.tenant_id == Tenant.id).correlate(Tenant).scalar_subquery()
    workflow_count_sq = select(func.count(Workflow.id)).where(Workflow.tenant_id == Tenant.id).correlate(Tenant).scalar_subquery()
    run_count_sq = select(func.count(WorkflowRun.id)).where(WorkflowRun.tenant_id == Tenant.id).correlate(Tenant).scalar_subquery()
    cost_sq = select(func.coalesce(func.sum(AIProviderCall.cost_usd), 0)).where(AIProviderCall.tenant_id == Tenant.id).correlate(Tenant).scalar_subquery()
    tenant_rows = await db.execute(
        select(Tenant, user_count_sq.label("users"), workflow_count_sq.label("workflows"), run_count_sq.label("runs"), cost_sq.label("cost_usd"))
        .order_by(Tenant.created_at.desc())
        .limit(100)
    )
    tenant_items = []
    for tenant, user_count, workflow_count, run_count, cost_usd in tenant_rows.all():
        tenant_items.append({
            "id": tenant.id, "name": tenant.name, "slug": tenant.slug, "status": tenant.status,
            "users": int(user_count or 0), "workflows": int(workflow_count or 0),
            "runs": int(run_count or 0), "cost_usd": float(cost_usd or 0), "created_at": tenant.created_at,
        })

    provider_rows = await db.execute(
        select(
            AIProviderCall.provider,
            func.count(AIProviderCall.id).label("calls"),
            func.sum(cast(AIProviderCall.status == "success", Integer)).label("successful_calls"),
            func.sum(cast(AIProviderCall.status != "success", Integer)).label("failed_calls"),
            func.coalesce(func.sum(AIProviderCall.prompt_tokens + AIProviderCall.completion_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(AIProviderCall.cost_usd), 0).label("cost_usd"),
            func.coalesce(func.avg(AIProviderCall.latency_ms), 0).label("avg_latency_ms"),
        ).group_by(AIProviderCall.provider).order_by(func.count(AIProviderCall.id).desc())
    )
    providers = [
        {"provider": row.provider, "calls": int(row.calls or 0), "successful_calls": int(row.successful_calls or 0),
         "failed_calls": int(row.failed_calls or 0), "total_tokens": int(row.total_tokens or 0),
         "cost_usd": float(row.cost_usd or 0), "avg_latency_ms": float(row.avg_latency_ms or 0)}
        for row in provider_rows.all()
    ]

    # Dependency health is deliberately conservative: DB is known healthy if this query completed.
    return {
        "tenants": int(tenants), "active_tenants": int(active_tenants), "users": int(users),
        "workflows": int(workflows), "workflow_runs": int(workflow_runs), "ai_calls": int(ai_calls),
        "total_tokens": int(total_tokens or 0), "total_cost_usd": float(total_cost or 0),
        "failed_runs": int(failed_runs), "pending_outbox": int(pending_outbox), "dead_outbox": int(dead_outbox),
        "tenants_breakdown": tenant_items, "providers": providers,
        "health": await _health(),
    }

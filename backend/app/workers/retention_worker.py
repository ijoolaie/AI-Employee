"""Read-only scheduled preview of tenant retention candidates.

This worker deliberately does not call enforce_retention or issue mutations.
Destructive execution remains an explicit, separately authorized operation.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select

from app.core.config import get_settings
from app.core.database import worker_db_session
from app.models.customer_conversation_slot import CustomerConversationSlot
from app.models.file import FileObject
from app.models.memory import EmployeeMemory
from app.models.tenant import Tenant
from app.models.usage import UsageEvent
from app.services.retention_service import DEFAULT_RETENTION_DAYS
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.retention")

_COUNT_KEYS = (
    "usage_events_eligible",
    "memory_rows_eligible",
    "files_eligible_for_soft_delete",
    "customer_slots_eligible_for_purge",
)


async def _count(db, model, *criteria) -> int:
    result = await db.execute(select(func.count()).select_from(model).where(*criteria))
    return int(result.scalar_one())


async def _retention_dry_run_async() -> dict:
    settings = get_settings()
    retention_days = int(getattr(settings, "data_retention_days", DEFAULT_RETENTION_DAYS))
    if not 1 <= retention_days <= 3650:
        raise ValueError("data_retention_days must be between 1 and 3650")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    tenant_results: list[dict[str, int | str]] = []

    async with worker_db_session() as db:
        tenant_result = await db.execute(
            select(Tenant.id).where(Tenant.status != "deleted").order_by(Tenant.id)
        )
        tenant_ids = list(tenant_result.scalars().all())

        for tenant_id in tenant_ids:
            counts = {
                "usage_events_eligible": await _count(
                    db, UsageEvent,
                    UsageEvent.tenant_id == tenant_id,
                    UsageEvent.created_at < cutoff,
                ),
                "memory_rows_eligible": await _count(
                    db, EmployeeMemory,
                    EmployeeMemory.tenant_id == tenant_id,
                    or_(
                        EmployeeMemory.expires_at <= now,
                        and_(
                            EmployeeMemory.created_at < cutoff,
                            EmployeeMemory.status.in_(["expired", "deleted", "superseded"]),
                        ),
                    ),
                ),
                "files_eligible_for_soft_delete": await _count(
                    db, FileObject,
                    FileObject.tenant_id == tenant_id,
                    FileObject.created_at < cutoff,
                    FileObject.status == "active",
                ),
                "customer_slots_eligible_for_purge": await _count(
                    db, CustomerConversationSlot,
                    CustomerConversationSlot.tenant_id == tenant_id,
                    CustomerConversationSlot.expires_at <= now,
                ),
            }
            tenant_summary = {"tenant_id": str(tenant_id), **counts}
            tenant_results.append(tenant_summary)
            logger.info("retention_dry_run_tenant", extra=tenant_summary)

    totals = {key: sum(int(item[key]) for item in tenant_results) for key in _COUNT_KEYS}
    summary = {
        "mode": "dry_run",
        "retention_days": retention_days,
        "tenants_scanned": len(tenant_results),
        "tenant_counts": tenant_results,
        "totals": totals,
        "enforced_at": now.isoformat(),
        "mutations_performed": False,
    }
    logger.info(
        "retention_dry_run_completed",
        extra={
            "mode": summary["mode"],
            "retention_days": retention_days,
            "tenants_scanned": len(tenant_results),
            "totals": totals,
            "mutations_performed": False,
        },
    )
    return summary


@celery_app.task(name="retention.dry_run")
def retention_dry_run_task() -> dict:
    """Report per-tenant retention candidates without modifying database rows."""
    return asyncio.run(_retention_dry_run_async())

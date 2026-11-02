"""Run a read-only, tenant-scoped preview of retention candidates."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models.customer_conversation_slot import CustomerConversationSlot
from app.models.file import FileObject
from app.models.memory import EmployeeMemory
from app.models.tenant import Tenant
from app.models.usage import UsageEvent
from app.services.retention_service import DEFAULT_RETENTION_DAYS


COUNT_KEYS = (
    "usage_events_eligible",
    "memory_rows_eligible",
    "files_eligible_for_soft_delete",
    "customer_slots_eligible_for_purge",
)


async def _count(db, model, *criteria) -> int:
    result = await db.execute(select(func.count()).select_from(model).where(*criteria))
    return int(result.scalar_one())


async def build_retention_preview() -> dict:
    """Count eligible rows only; enforce PostgreSQL read-only transaction semantics."""
    settings = get_settings()
    retention_days = int(getattr(settings, "data_retention_days", DEFAULT_RETENTION_DAYS))
    if not 1 <= retention_days <= 3650:
        raise ValueError("data_retention_days must be between 1 and 3650")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    tenant_results: list[dict[str, int | str]] = []
    try:
        async with session_factory() as db:
            await db.execute(text("SET TRANSACTION READ ONLY"))
            tenant_result = await db.execute(
                select(Tenant.id).where(Tenant.status != "deleted").order_by(Tenant.id)
            )
            tenant_ids = list(tenant_result.scalars().all())
            for tenant_id in tenant_ids:
                counts = {
                    "usage_events_eligible": await _count(
                        db, UsageEvent, UsageEvent.tenant_id == tenant_id, UsageEvent.created_at < cutoff
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
                tenant_results.append({"tenant_id": str(tenant_id), **counts})
    finally:
        await engine.dispose()

    totals = {key: sum(int(row[key]) for row in tenant_results) for key in COUNT_KEYS}
    return {
        "mode": "dry_run",
        "retention_days": retention_days,
        "tenants_scanned": len(tenant_results),
        "tenant_counts": tenant_results,
        "totals": totals,
        "observed_at": now.isoformat(),
        "mutations_performed": False,
        "database_transaction": "READ ONLY",
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(build_retention_preview()), indent=2, sort_keys=True))

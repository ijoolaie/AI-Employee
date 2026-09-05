"""Run the configured retention policy for every active tenant.

Usage from the backend environment:
    python -m scripts.enforce_retention

No secrets are accepted on the command line. The database URL is resolved
through the application's normal runtime configuration.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.services.retention_service import DEFAULT_RETENTION_DAYS, enforce_retention


async def main() -> None:
    settings = get_settings()
    retention_days = int(getattr(settings, "DATA_RETENTION_DAYS", DEFAULT_RETENTION_DAYS))
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant.id).where(Tenant.status != "deleted"))
        tenant_ids = list(result.scalars().all())
        totals: dict[str, int] = {}
        for tenant_id in tenant_ids:
            outcome = await enforce_retention(
                db, tenant_id=tenant_id, retention_days=retention_days
            )
            for key, value in outcome.items():
                if key in {"tenant_id", "cutoff", "enforced_at"}:
                    continue
                totals[key] = totals.get(key, 0) + int(value)
        await db.commit()
    print({"tenants": len(tenant_ids), "retention_days": retention_days, **totals})


if __name__ == "__main__":
    asyncio.run(main())

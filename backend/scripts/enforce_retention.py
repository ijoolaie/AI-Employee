"""Run the configured retention policy for every active tenant.

Safe by default: the script performs a dry-run unless ``--execute`` is passed.

Usage from the backend environment:
    python -m scripts.enforce_retention
    python -m scripts.enforce_retention --execute

No secrets are accepted on the command line. The database URL is resolved
through the application's normal runtime configuration.
"""
from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.services.retention_service import DEFAULT_RETENTION_DAYS, enforce_retention


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enforce tenant data-retention policy safely.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform destructive retention actions. Without this flag the command is dry-run only.",
    )
    return parser.parse_args()


async def main(*, execute: bool) -> None:
    settings = get_settings()
    retention_days = int(getattr(settings, "data_retention_days", DEFAULT_RETENTION_DAYS))
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant.id).where(Tenant.status != "deleted"))
        tenant_ids = list(result.scalars().all())

        if not execute:
            print(
                {
                    "mode": "dry-run",
                    "tenants": len(tenant_ids),
                    "retention_days": retention_days,
                    "message": "No records were modified. Re-run with --execute to enforce the policy.",
                }
            )
            return

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
    print({"mode": "execute", "tenants": len(tenant_ids), "retention_days": retention_days, **totals})


if __name__ == "__main__":
    asyncio.run(main(execute=parse_args().execute))

"""Safely remove legacy tenant/RBAC certification fixtures.

Dry-run by default. Pass --apply to commit deletion.
Only tenants with the exact certification slug prefixes are eligible:
  cert-a-* / cert-b-*
No production/test tenants with unrelated slugs are touched.
"""
from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import delete, exists, or_, select
from sqlalchemy.sql.schema import Table

from app.core.database import AsyncSessionLocal, Base
from app.models.tenant import Tenant

PREFIXES = ("cert-a-", "cert-b-")


def cleanup_predicates(tenant_ids: list) -> dict[Table, object]:
    tables = list(Base.metadata.sorted_tables)
    tenant_table = Tenant.__table__
    scoped_tables = {tenant_table}

    changed = True
    while changed:
        changed = False
        for table in tables:
            if table in scoped_tables:
                continue
            if "tenant_id" in table.c or any(
                fk.column.table in scoped_tables
                for column in table.columns
                for fk in column.foreign_keys
            ):
                scoped_tables.add(table)
                changed = True

    predicates: dict[Table, object] = {tenant_table: tenant_table.c.id.in_(tenant_ids)}
    for table in tables:
        if table is tenant_table:
            continue
        clauses: list[object] = []
        if "tenant_id" in table.c:
            clauses.append(table.c.tenant_id.in_(tenant_ids))
        for constraint in table.foreign_key_constraints:
            parent = constraint.referred_table
            parent_predicate = predicates.get(parent)
            if parent not in scoped_tables or parent_predicate is None:
                continue
            clauses.append(
                exists(
                    select(1).select_from(parent).where(
                        parent_predicate,
                        *[element.parent == element.column for element in constraint.elements],
                    )
                )
            )
        if clauses:
            predicates[table] = or_(*clauses)
    return predicates


async def main(apply: bool) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Tenant.id, Tenant.slug, Tenant.name)
            .where(or_(*(Tenant.slug.like(f"{prefix}%") for prefix in PREFIXES)))
            .order_by(Tenant.slug)
        )
        tenants = result.all()
        print(f"Eligible certification tenants: {len(tenants)}")
        for tenant_id, slug, name in tenants:
            print(f"  {tenant_id}  {slug}  {name}")

        if not tenants:
            return
        if not apply:
            print("DRY RUN ONLY: no rows deleted. Re-run with --apply to delete these fixtures.")
            return

        tenant_ids = [row[0] for row in tenants]
        predicates = cleanup_predicates(tenant_ids)
        counts: list[tuple[str, int]] = []
        for table in reversed(Base.metadata.sorted_tables):
            predicate = predicates.get(table)
            if predicate is None:
                continue
            result = await db.execute(delete(table).where(predicate))
            if result.rowcount:
                counts.append((table.name, result.rowcount))

        await db.commit()
        print("CLEANUP COMMITTED")
        for table, count in counts:
            print(f"  {table}: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="commit the deletion; otherwise dry-run")
    args = parser.parse_args()
    asyncio.run(main(args.apply))

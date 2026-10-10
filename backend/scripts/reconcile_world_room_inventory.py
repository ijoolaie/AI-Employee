"""Audit and optionally backfill legacy room inventory in a tenant-scoped, dry-run-first way.

Dry-run is the default. Applying changes requires --apply --confirm --tenant-id.
Only active room entitlements with an active room catalogue item and a future,
explicit expiry are eligible. This script never extends leases, changes entitlements,
unsuspends inventory, or repairs missing-expiry/expired records automatically.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.world_commerce import WorldCatalogueItem, WorldFeatureEntitlement, WorldRoomInventory


def classify_room_entitlement(
    entitlement: WorldFeatureEntitlement,
    catalogue: WorldCatalogueItem | None,
    inventory: WorldRoomInventory | None,
    *,
    now: datetime,
) -> str:
    """Return a report status; only 'eligible_to_backfill' permits a write."""
    if catalogue is None:
        return "missing_catalogue_item"
    if catalogue.item_type != "room":
        return "catalogue_item_not_room"
    if not catalogue.is_active:
        return "catalogue_item_inactive"
    if inventory is not None:
        if inventory.entitlement_id != entitlement.id:
            return "inventory_entitlement_mismatch"
        if inventory.status == "suspended":
            return "inventory_suspended_manual_review"
        if entitlement.status != "active":
            return "inventory_with_inactive_entitlement"
        if entitlement.expires_at is None:
            return "existing_inventory_missing_expiry"
        if entitlement.expires_at <= now:
            return "existing_inventory_expired_lease"
        return "already_consistent"
    if entitlement.status != "active":
        return "inactive_entitlement_missing_inventory"
    if entitlement.expires_at is None:
        return "active_entitlement_missing_expiry_manual_review"
    if entitlement.expires_at <= now:
        return "expired_entitlement_missing_inventory"
    return "eligible_to_backfill"


async def reconcile_room_inventory(
    session: AsyncSession,
    *,
    tenant_id: UUID | None,
    apply: bool,
    now: datetime | None = None,
) -> dict:
    """Create inventory only for safe candidates; dry-run performs no writes."""
    now = now or datetime.now(timezone.utc)
    entitlement_stmt = select(WorldFeatureEntitlement).where(WorldFeatureEntitlement.item_type == "room")
    if tenant_id is not None:
        entitlement_stmt = entitlement_stmt.where(WorldFeatureEntitlement.tenant_id == tenant_id)
    if apply:
        entitlement_stmt = entitlement_stmt.with_for_update()

    entitlements = list((await session.scalars(entitlement_stmt)).all())
    catalogue_items = list((await session.scalars(select(WorldCatalogueItem))).all())
    inventory_stmt = select(WorldRoomInventory)
    if tenant_id is not None:
        inventory_stmt = inventory_stmt.where(WorldRoomInventory.tenant_id == tenant_id)
    inventories = list((await session.scalars(inventory_stmt)).all())

    catalogue_by_code = {item.code: item for item in catalogue_items}
    inventory_by_key = {(item.tenant_id, item.item_code): item for item in inventories}
    counts: Counter[str] = Counter()
    records: list[dict] = []
    inserted: list[dict] = []

    for entitlement in entitlements:
        catalogue = catalogue_by_code.get(entitlement.item_code)
        inventory = inventory_by_key.get((entitlement.tenant_id, entitlement.item_code))
        status = classify_room_entitlement(entitlement, catalogue, inventory, now=now)
        counts[status] += 1
        record = {
            "tenant_id": str(entitlement.tenant_id),
            "item_code": entitlement.item_code,
            "entitlement_id": str(entitlement.id),
            "inventory_id": str(inventory.id) if inventory is not None else None,
            "classification": status,
        }
        records.append(record)

        if apply and status == "eligible_to_backfill":
            # The entitlement row is locked in apply mode; uniqueness constraints remain
            # the final guard against duplicate tenant/item or entitlement inventory.
            new_inventory = WorldRoomInventory(
                id=uuid4(),
                tenant_id=entitlement.tenant_id,
                entitlement_id=entitlement.id,
                item_code=entitlement.item_code,
                status="provisioned",
                scene_config={},
            )
            session.add(new_inventory)
            inventory_by_key[(entitlement.tenant_id, entitlement.item_code)] = new_inventory
            record["inventory_id"] = str(new_inventory.id)
            record["classification"] = "backfilled"
            inserted.append({
                "tenant_id": str(entitlement.tenant_id),
                "item_code": entitlement.item_code,
                "entitlement_id": str(entitlement.id),
                "inventory_id": str(new_inventory.id),
            })

    if apply and inserted:
        await session.flush()
        await session.commit()

    return {
        "mode": "apply" if apply else "dry-run",
        "tenant_scope": str(tenant_id) if tenant_id is not None else "all-tenants",
        "generated_at": now.isoformat(),
        "counts": dict(sorted(counts.items())),
        "eligible_to_backfill": counts["eligible_to_backfill"],
        "backfilled": len(inserted),
        "inserted": inserted,
        "records": records,
        "writes_performed": bool(inserted),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", type=UUID, help="Limit the audit/apply run to one tenant UUID.")
    parser.add_argument("--apply", action="store_true", help="Create missing inventory for eligible active room leases.")
    parser.add_argument("--confirm", action="store_true", help="Required with --apply to confirm this explicit repair.")
    args = parser.parse_args(argv)
    if args.apply and not args.confirm:
        parser.error("--apply requires --confirm")
    if args.apply and args.tenant_id is None:
        parser.error("--apply requires --tenant-id; broad all-tenant writes are prohibited")
    if args.confirm and not args.apply:
        parser.error("--confirm is only valid with --apply")
    return args


async def _run(args: argparse.Namespace) -> dict:
    async with AsyncSessionLocal() as session:
        try:
            return await reconcile_room_inventory(session, tenant_id=args.tenant_id, apply=args.apply)
        except Exception:
            await session.rollback()
            raise


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = asyncio.run(_run(args))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    raise SystemExit(main())

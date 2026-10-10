from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from scripts.reconcile_world_room_inventory import (
    classify_room_entitlement,
    parse_args,
    reconcile_room_inventory,
)

_UNSET = object()


def _fixtures(*, status="active", expires_at=_UNSET, catalogue_active=True, inventory_status=None):
    now = datetime.now(timezone.utc)
    tenant_id = uuid4()
    entitlement_id = uuid4()
    entitlement = SimpleNamespace(
        id=entitlement_id,
        tenant_id=tenant_id,
        item_code="room.starter",
        item_type="room",
        status=status,
        expires_at=now + timedelta(days=3) if expires_at is _UNSET else expires_at,
    )
    catalogue = SimpleNamespace(code="room.starter", item_type="room", is_active=catalogue_active)
    inventory = None
    if inventory_status is not None:
        inventory = SimpleNamespace(
            id=uuid4(),
            tenant_id=tenant_id,
            item_code="room.starter",
            entitlement_id=entitlement_id,
            status=inventory_status,
        )
    return now, entitlement, catalogue, inventory


def test_reconciliation_only_eligible_for_active_room_with_future_explicit_expiry():
    now, entitlement, catalogue, inventory = _fixtures()
    assert classify_room_entitlement(entitlement, catalogue, inventory, now=now) == "eligible_to_backfill"


def test_reconciliation_never_repairs_missing_or_expired_lease_implicitly():
    now, entitlement, catalogue, inventory = _fixtures(expires_at=None)
    assert classify_room_entitlement(entitlement, catalogue, inventory, now=now) == "active_entitlement_missing_expiry_manual_review"

    now, entitlement, catalogue, inventory = _fixtures(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    assert classify_room_entitlement(entitlement, catalogue, inventory, now=now) == "expired_entitlement_missing_inventory"


def test_reconciliation_does_not_unsuspend_or_repair_inconsistent_inventory():
    now, entitlement, catalogue, inventory = _fixtures(inventory_status="suspended")
    assert classify_room_entitlement(entitlement, catalogue, inventory, now=now) == "inventory_suspended_manual_review"

    now, entitlement, catalogue, inventory = _fixtures()
    inventory = SimpleNamespace(id=uuid4(), tenant_id=entitlement.tenant_id, item_code=entitlement.item_code, entitlement_id=uuid4(), status="provisioned")
    assert classify_room_entitlement(entitlement, catalogue, inventory, now=now) == "inventory_entitlement_mismatch"


def test_reconciliation_rejects_inactive_catalogue_and_revoked_entitlements():
    now, entitlement, catalogue, inventory = _fixtures(catalogue_active=False)
    assert classify_room_entitlement(entitlement, catalogue, inventory, now=now) == "catalogue_item_inactive"

    now, entitlement, catalogue, inventory = _fixtures(status="revoked")
    assert classify_room_entitlement(entitlement, catalogue, inventory, now=now) == "inactive_entitlement_missing_inventory"


def test_reconciliation_cli_requires_explicit_scoped_confirmation_for_writes():
    args = parse_args([])
    assert args.apply is False
    assert args.tenant_id is None

    with pytest.raises(SystemExit):
        parse_args(["--apply"])
    with pytest.raises(SystemExit):
        parse_args(["--apply", "--confirm"])
    with pytest.raises(SystemExit):
        parse_args(["--confirm"])
    tenant_id = uuid4()
    args = parse_args(["--apply", "--confirm", "--tenant-id", str(tenant_id)])
    assert args.apply is True
    assert args.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_reconciliation_dry_run_is_read_only():
    now, entitlement, catalogue, _ = _fixtures()
    session = AsyncMock()
    session.scalars.side_effect = [
        SimpleNamespace(all=lambda: [entitlement]),
        SimpleNamespace(all=lambda: [catalogue]),
        SimpleNamespace(all=lambda: []),
    ]

    report = await reconcile_room_inventory(session, tenant_id=entitlement.tenant_id, apply=False, now=now)

    assert report["mode"] == "dry-run"
    assert report["eligible_to_backfill"] == 1
    assert report["backfilled"] == 0
    assert report["writes_performed"] is False
    session.add.assert_not_called()
    session.flush.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconciliation_apply_backfills_only_safe_candidates_and_is_auditable():
    now, eligible, catalogue, _ = _fixtures()
    session = AsyncMock()
    session.scalars.side_effect = [
        SimpleNamespace(all=lambda: [eligible]),
        SimpleNamespace(all=lambda: [catalogue]),
        SimpleNamespace(all=lambda: []),
    ]

    report = await reconcile_room_inventory(session, tenant_id=eligible.tenant_id, apply=True, now=now)

    assert report["mode"] == "apply"
    assert report["backfilled"] == 1
    assert report["writes_performed"] is True
    assert report["inserted"][0]["entitlement_id"] == str(eligible.id)
    assert report["records"][0]["classification"] == "backfilled"
    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.commit.assert_awaited_once()

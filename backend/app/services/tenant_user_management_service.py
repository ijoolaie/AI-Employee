"""Persisted tenant-ancestry authorization for delegated user administration."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.services.edition_service import EDITION_CUSTOMER, EDITION_RESELLER, EDITION_VENDOR


def _deny() -> None:
    raise HTTPException(status_code=403, detail="Tenant is outside the permitted user-management hierarchy")


def _validate_root_vendor(vendor: Tenant) -> None:
    if vendor.tenant_kind != EDITION_VENDOR or vendor.parent_tenant_id is not None or vendor.status != "active":
        _deny()


def _validate_actor(actor: Tenant, actor_parent: Tenant | None) -> None:
    if actor.status != "active":
        raise HTTPException(status_code=403, detail="Actor tenant is inactive")
    if actor.tenant_kind == EDITION_VENDOR:
        _validate_root_vendor(actor)
        return
    if actor.tenant_kind == EDITION_RESELLER and actor_parent is not None:
        _validate_root_vendor(actor_parent)
        if actor.parent_tenant_id != actor_parent.id:
            _deny()
        return
    _deny()


def _validate_target(actor: Tenant, target: Tenant, target_parent: Tenant | None, target_grandparent: Tenant | None) -> None:
    if target.status != "active":
        raise HTTPException(status_code=403, detail="Target tenant is inactive")
    if target.id == actor.id:
        _deny()

    if actor.tenant_kind == EDITION_VENDOR:
        if target.tenant_kind == EDITION_RESELLER and target_parent is not None:
            _validate_root_vendor(actor)
            if target.parent_tenant_id == actor.id and target_parent.id == actor.id:
                return
        elif target.tenant_kind == EDITION_CUSTOMER and target_parent is not None:
            _validate_root_vendor(actor)
            if target.parent_tenant_id == actor.id and target_parent.id == actor.id:
                return
            if target_parent.tenant_kind == EDITION_RESELLER and target_parent.parent_tenant_id == actor.id:
                if target_grandparent is not None and target_grandparent.id == actor.id:
                    _validate_root_vendor(target_grandparent)
                    if target_parent.status == "active":
                        return
        _deny()

    if actor.tenant_kind == EDITION_RESELLER and target.tenant_kind == EDITION_CUSTOMER:
        if target_parent is not None and target_parent.id == actor.id and target.parent_tenant_id == actor.id:
            return
    _deny()


async def resolve_user_management_target(
    db: AsyncSession, *, actor_tenant_id: UUID, target_tenant_id: UUID
) -> Tenant:
    """Return an active child tenant only when persisted ancestry authorizes it."""
    actor = (await db.execute(select(Tenant).where(Tenant.id == actor_tenant_id))).scalar_one_or_none()
    if actor is None:
        raise HTTPException(status_code=403, detail="Actor tenant is unavailable")

    target = (await db.execute(select(Tenant).where(Tenant.id == target_tenant_id))).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="Target tenant not found")

    parent_ids = {value for value in (actor.parent_tenant_id, target.parent_tenant_id) if value is not None}
    parents = {}
    if parent_ids:
        rows = (await db.execute(select(Tenant).where(Tenant.id.in_(parent_ids)))).scalars().all()
        parents = {row.id: row for row in rows}
    actor_parent = parents.get(actor.parent_tenant_id)
    target_parent = parents.get(target.parent_tenant_id)

    grandparent = None
    if target_parent is not None and target_parent.parent_tenant_id is not None:
        grandparent = (await db.execute(
            select(Tenant).where(Tenant.id == target_parent.parent_tenant_id)
        )).scalar_one_or_none()

    _validate_actor(actor, actor_parent)
    _validate_target(actor, target, target_parent, grandparent)
    return target

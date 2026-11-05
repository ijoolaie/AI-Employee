"""Lifecycle and validation for explicit portal access grants."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal_access_grant import PortalAccessGrant
from app.models.tenant import Tenant
from app.models.user import User
from app.services import audit_service
from app.services.tenant_access_service import tenant_has_access
from app.services.edition_service import EDITION_CUSTOMER, EDITION_RESELLER, EDITION_VENDOR


def _assert_direct_portal_edge(actor_tenant: Tenant, target_tenant: Tenant) -> None:
    allowed = (
        actor_tenant.tenant_kind == EDITION_VENDOR
        and target_tenant.tenant_kind in {EDITION_RESELLER, EDITION_CUSTOMER}
    ) or (
        actor_tenant.tenant_kind == EDITION_RESELLER
        and target_tenant.tenant_kind == EDITION_CUSTOMER
    )
    if not allowed or target_tenant.parent_tenant_id != actor_tenant.id:
        raise HTTPException(status_code=403, detail="Portal access requires a permitted direct child tenant")


async def create_portal_access_grant(
    db: AsyncSession,
    *,
    grantor: User,
    actor_user_id: UUID,
    target_tenant_id: UUID,
    reason: str,
) -> PortalAccessGrant:
    reason = reason.strip()
    if not reason:
        raise HTTPException(status_code=422, detail="A reason is required")
    actor_tenant = (await db.execute(select(Tenant).where(Tenant.id == grantor.tenant_id))).scalar_one_or_none()
    target = (await db.execute(select(Tenant).where(Tenant.id == target_tenant_id).with_for_update())).scalar_one_or_none()
    actor = (await db.execute(select(User).where(User.id == actor_user_id).with_for_update())).scalar_one_or_none()
    if actor_tenant is None or target is None or actor is None:
        raise HTTPException(status_code=404, detail="Portal access target or user not found")
    if not grantor.is_active or not actor.is_active or actor.tenant_id != grantor.tenant_id:
        raise HTTPException(status_code=403, detail="Portal grants are limited to active users in the granting tenant")
    if actor_tenant.status != "active" or target.status != "active":
        raise HTTPException(status_code=403, detail="Both tenants must be active")
    _assert_direct_portal_edge(actor_tenant, target)
    if not await tenant_has_access(db, tenant=target):
        raise HTTPException(status_code=402, detail="Target tenant requires an approved paid subscription or active Demo grant")

    existing = (await db.execute(
        select(PortalAccessGrant)
        .where(
            PortalAccessGrant.actor_user_id == actor.id,
            PortalAccessGrant.actor_tenant_id == actor_tenant.id,
            PortalAccessGrant.target_tenant_id == target.id,
            PortalAccessGrant.revoked_at.is_(None),
        )
        .with_for_update()
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="An active portal grant already exists")

    grant = PortalAccessGrant(
        actor_user_id=actor.id,
        actor_tenant_id=actor_tenant.id,
        target_tenant_id=target.id,
        granted_by_user_id=grantor.id,
        reason=reason,
    )
    db.add(grant)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=actor_tenant.id,
        actor_id=grantor.id,
        action="portal_access.granted",
        resource_type="portal_access_grant",
        resource_id=str(grant.id),
        metadata={"actor_user_id": str(actor.id), "actor_tenant_id": str(actor_tenant.id), "target_tenant_id": str(target.id), "reason": reason},
    )
    return grant


async def revoke_portal_access_grant(
    db: AsyncSession,
    *,
    grantor: User,
    grant_id: UUID,
) -> PortalAccessGrant:
    result = await db.execute(
        select(PortalAccessGrant)
        .where(
            PortalAccessGrant.id == grant_id,
            PortalAccessGrant.actor_tenant_id == grantor.tenant_id,
        )
        .with_for_update()
    )
    grant = result.scalar_one_or_none()
    if grant is None:
        raise HTTPException(status_code=404, detail="Portal access grant not found")
    if grant.revoked_at is not None:
        return grant
    grant.revoked_at = datetime.now(timezone.utc)
    await audit_service.record(
        db,
        tenant_id=grant.actor_tenant_id,
        actor_id=grantor.id,
        action="portal_access.revoked",
        resource_type="portal_access_grant",
        resource_id=str(grant.id),
        metadata={"actor_user_id": str(grant.actor_user_id), "actor_tenant_id": str(grant.actor_tenant_id), "target_tenant_id": str(grant.target_tenant_id)},
    )
    await db.flush()
    return grant


async def validate_portal_access_grant(
    db: AsyncSession,
    *,
    actor_user_id: UUID,
    actor_tenant_id: UUID,
    target_tenant_id: UUID,
    grant_id: UUID,
) -> PortalAccessGrant:
    """Fail-closed lookup intended for every portal-context request."""
    result = await db.execute(
        select(PortalAccessGrant)
        .join(User, User.id == PortalAccessGrant.actor_user_id)
        .join(Tenant, Tenant.id == PortalAccessGrant.target_tenant_id)
        .where(
            PortalAccessGrant.actor_user_id == actor_user_id,
            PortalAccessGrant.actor_tenant_id == actor_tenant_id,
            PortalAccessGrant.target_tenant_id == target_tenant_id,
            PortalAccessGrant.id == grant_id,
            PortalAccessGrant.revoked_at.is_(None),
            User.tenant_id == actor_tenant_id,
            User.is_active.is_(True),
            Tenant.status == "active",
        )
    )
    grant = result.scalar_one_or_none()
    if grant is None:
        raise HTTPException(status_code=403, detail="Active portal access grant required")
    actor_tenant = (await db.execute(select(Tenant).where(Tenant.id == actor_tenant_id))).scalar_one_or_none()
    target_tenant = (await db.execute(select(Tenant).where(Tenant.id == target_tenant_id))).scalar_one_or_none()
    if actor_tenant is None or target_tenant is None or actor_tenant.status != "active" or target_tenant.status != "active":
        raise HTTPException(status_code=403, detail="Portal tenant is unavailable")
    _assert_direct_portal_edge(actor_tenant, target_tenant)
    if not await tenant_has_access(db, tenant=target_tenant):
        raise HTTPException(status_code=402, detail="Target tenant commercial entitlement is inactive")
    return grant

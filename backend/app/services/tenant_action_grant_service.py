"""Create, revoke, and check user-bound edition action grants."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.tenant_action_grant import TenantActionGrant
from app.models.user import User
from app.services import audit_service
from app.services.edition_service import EDITION_CUSTOMER, EDITION_RESELLER, EDITION_VENDOR

VENDOR_ACTION_CODES = frozenset({
    "vendor.tenant.read",
    "vendor.reseller.read",
    "vendor.reseller.create",
    "vendor.reseller.manage",
    "vendor.customer.read",
    "vendor.customer.create",
    "vendor.customer.manage",
})
RESELLER_ACTION_CODES = frozenset({
    "reseller.customer.create",
    "reseller.customer.read",
    "reseller.customer.manage",
    "reseller.entitlement.delegate",
})


def _allowed_codes(tenant_kind: str) -> frozenset[str]:
    if tenant_kind == EDITION_VENDOR:
        return VENDOR_ACTION_CODES
    if tenant_kind == EDITION_RESELLER:
        return RESELLER_ACTION_CODES
    return frozenset()


def _grantor_holds_action(grantor: User, action_code: str) -> bool:
    return any(
        permission.code == action_code
        for role in grantor.roles
        if role.tenant_id == grantor.tenant_id
        for permission in role.permissions
    )


async def create_tenant_action_grant(
    db: AsyncSession,
    *,
    grantor: User,
    target_user_id: UUID,
    action_code: str,
    reason: str,
    expires_in_days: int = 90,
) -> TenantActionGrant:
    reason = reason.strip()
    if not reason:
        raise HTTPException(status_code=422, detail="A reason is required")
    if not 1 <= expires_in_days <= 90:
        raise HTTPException(status_code=422, detail="Action grants must expire within 1 to 90 days")
    tenant = (await db.execute(
        select(Tenant).where(Tenant.id == grantor.tenant_id).with_for_update()
    )).scalar_one_or_none()
    if tenant is None or tenant.status != "active":
        raise HTTPException(status_code=403, detail="Granting tenant is unavailable")
    if action_code not in _allowed_codes(tenant.tenant_kind):
        raise HTTPException(status_code=403, detail="Action is not grantable in this tenant edition")
    # A grantor can delegate only an action they hold directly through a
    # tenant-local role. A received user grant cannot be re-delegated.
    if not _grantor_holds_action(grantor, action_code):
        raise HTTPException(status_code=403, detail="Grantor cannot delegate an action they do not hold directly")

    target_user = (await db.execute(
        select(User).where(User.id == target_user_id).with_for_update()
    )).scalar_one_or_none()
    if target_user is None or not target_user.is_active or target_user.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="Active user in the granting tenant not found")

    existing = (await db.execute(
        select(TenantActionGrant).where(
            TenantActionGrant.user_id == target_user.id,
            TenantActionGrant.tenant_id == tenant.id,
            TenantActionGrant.action_code == action_code,
            TenantActionGrant.revoked_at.is_(None),
        ).with_for_update()
    )).scalar_one_or_none()
    if existing is not None:
        now = datetime.now(timezone.utc)
        if existing.expires_at > now:
            raise HTTPException(status_code=409, detail="An active action grant already exists")
        existing.revoked_at = now
        await audit_service.record(
            db, tenant_id=tenant.id, actor_id=grantor.id,
            action="tenant_action_grant.expired", resource_type="tenant_action_grant",
            resource_id=str(existing.id),
            metadata={"user_id": str(target_user.id), "tenant_id": str(tenant.id), "action_code": action_code},
        )

    grant = TenantActionGrant(
        user_id=target_user.id,
        tenant_id=tenant.id,
        action_code=action_code,
        granted_by_user_id=grantor.id,
        reason=reason,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
    )
    db.add(grant)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant.id,
        actor_id=grantor.id,
        action="tenant_action_grant.created",
        resource_type="tenant_action_grant",
        resource_id=str(grant.id),
        metadata={
            "user_id": str(target_user.id),
            "tenant_id": str(tenant.id),
            "action_code": action_code,
            "expires_at": grant.expires_at.isoformat(),
            "reason": reason,
        },
    )
    return grant


async def revoke_tenant_action_grant(
    db: AsyncSession,
    *,
    grantor: User,
    grant_id: UUID,
) -> TenantActionGrant:
    grant = (await db.execute(
        select(TenantActionGrant).where(
            TenantActionGrant.id == grant_id,
            TenantActionGrant.tenant_id == grantor.tenant_id,
        ).with_for_update()
    )).scalar_one_or_none()
    if grant is None:
        raise HTTPException(status_code=404, detail="Action grant not found")
    if grant.revoked_at is not None:
        return grant
    grant.revoked_at = datetime.now(timezone.utc)
    await audit_service.record(
        db,
        tenant_id=grant.tenant_id,
        actor_id=grantor.id,
        action="tenant_action_grant.revoked",
        resource_type="tenant_action_grant",
        resource_id=str(grant.id),
        metadata={
            "user_id": str(grant.user_id),
            "tenant_id": str(grant.tenant_id),
            "action_code": grant.action_code,
        },
    )
    await db.flush()
    return grant


async def has_active_tenant_action_grant(
    db: AsyncSession,
    *,
    user_id: UUID,
    tenant_id: UUID,
    action_code: str,
) -> bool:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(TenantActionGrant.id).where(
            TenantActionGrant.user_id == user_id,
            TenantActionGrant.tenant_id == tenant_id,
            TenantActionGrant.action_code == action_code,
            TenantActionGrant.revoked_at.is_(None),
            TenantActionGrant.expires_at > now,
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None

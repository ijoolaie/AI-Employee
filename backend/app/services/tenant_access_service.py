"""Central tenant commercial access checks and audited Demo grants."""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError, TenantInactiveError, ValidationAppError
from app.models.billing import BillingPlan, Subscription
from app.models.tenant import Tenant
from app.models.tenant_demo_grant import TenantDemoGrant
from app.models.user import User
from app.models.tenant_invitation import TenantInvitation
from app.services import audit_service

async def tenant_access_source(db: AsyncSession, *, tenant: Tenant, now: datetime | None = None) -> str | None:
    """Return legacy, paid, or demo only when that source currently grants access."""
    if not getattr(tenant, "access_grant_required", False):
        return "legacy"
    now = now or datetime.now(timezone.utc)
    paid = (await db.execute(
        select(Subscription.id).join(BillingPlan, BillingPlan.id == Subscription.plan_id).where(
            Subscription.tenant_id == tenant.id, Subscription.status == "active",
            Subscription.provider == "stripe", BillingPlan.monthly_price_usd > 0,
            Subscription.current_period_end > now,
        ).limit(1)
    )).scalar_one_or_none()
    if paid is not None:
        return "paid"
    grant = (await db.execute(select(TenantDemoGrant.id).where(
        TenantDemoGrant.tenant_id == tenant.id, TenantDemoGrant.revoked_at.is_(None),
        TenantDemoGrant.expires_at > now,
    ).limit(1).with_for_update(read=True))).scalar_one_or_none()
    return "demo" if grant is not None else None


async def tenant_has_access(db: AsyncSession, *, tenant: Tenant, now: datetime | None = None) -> bool:
    return await tenant_access_source(db, tenant=tenant, now=now) is not None


async def assert_tenant_active_for_side_effect(db: AsyncSession, *, tenant_id: uuid.UUID) -> Tenant:
    """Lock the tenant lifecycle row through an irreversible provider call.

    Call only after the outbox uncertain fence is committed. The caller must
    keep this transaction open until the provider result is durably recorded.
    Tenant lifecycle transitions take the same row lock, giving suspension
    and delivery a single PostgreSQL serialization point.
    """
    tenant = (await db.execute(
        select(Tenant).where(Tenant.id == tenant_id).with_for_update()
    )).scalar_one_or_none()
    if tenant is None:
        raise TenantInactiveError("Tenant no longer exists; external delivery is blocked")
    if tenant.status != "active":
        raise TenantInactiveError()
    return tenant

async def create_demo_grant(db: AsyncSession, *, tenant_id: uuid.UUID, actor_id: uuid.UUID, reason: str, expires_in_days: int) -> TenantDemoGrant:
    if not reason.strip() or expires_in_days < 1 or expires_in_days > 90:
        raise ValidationAppError("Demo grant requires a reason and an expiry between 1 and 90 days")
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id).with_for_update())).scalar_one_or_none()
    if tenant is None:
        raise NotFoundError("Tenant not found")
    if not tenant.access_grant_required:
        raise ConflictError("Demo grants are available only for tenants that require an explicit access grant")
    grant = TenantDemoGrant(tenant_id=tenant_id, granted_by_user_id=actor_id, reason=reason.strip(), expires_at=datetime.now(timezone.utc)+timedelta(days=expires_in_days))
    db.add(grant)
    await db.flush()
    activated_public = await activate_pending_public_signup_users(db, tenant_id=tenant_id)
    from app.services.tenant_invitation_service import activate_eligible_invited_users
    activated_invited = await activate_eligible_invited_users(db, tenant_id=tenant_id)
    await audit_service.record(db, action="tenant.demo_grant_created", actor_type="user", actor_id=actor_id, tenant_id=tenant_id, resource_type="tenant_demo_grant", resource_id=str(grant.id), metadata={"reason": reason.strip(), "expires_at": grant.expires_at.isoformat(), "expires_in_days": expires_in_days, "activated_public_users": activated_public, "activated_invited_users": activated_invited})
    return grant

async def revoke_demo_grant(db: AsyncSession, *, tenant_id: uuid.UUID, grant_id: uuid.UUID, actor_id: uuid.UUID) -> TenantDemoGrant:
    grant = (await db.execute(select(TenantDemoGrant).where(TenantDemoGrant.id == grant_id, TenantDemoGrant.tenant_id == tenant_id).with_for_update())).scalar_one_or_none()
    if grant is None:
        raise NotFoundError("Demo grant not found")
    if grant.revoked_at is None:
        grant.revoked_at = datetime.now(timezone.utc)
        await audit_service.record(db, action="tenant.demo_grant_revoked", actor_type="user", actor_id=actor_id, tenant_id=tenant_id, resource_type="tenant_demo_grant", resource_id=str(grant.id), metadata={"expires_at": grant.expires_at.isoformat()})
    return grant


async def activate_pending_public_signup_users(db: AsyncSession, *, tenant_id: uuid.UUID) -> int:
    """Activate self-registered users after a paid or Demo entitlement; never activate invitees here."""
    users = (await db.execute(select(User).where(User.tenant_id == tenant_id, User.is_active.is_(False)).with_for_update())).scalars().all()
    activated = 0
    for user in users:
        invitation_id = (await db.execute(select(TenantInvitation.id).where(TenantInvitation.user_id == user.id).limit(1))).scalar_one_or_none()
        if invitation_id is not None:
            continue
        user.is_active = True
        user.auth_token_version += 1
        activated += 1
        await audit_service.record(db, action="tenant.public_signup_user_activated", actor_type="system", tenant_id=tenant_id, resource_type="user", resource_id=str(user.id), metadata={"grant_source": "tenant_access_entitlement"})
    return activated

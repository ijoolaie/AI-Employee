"""Secure tenant-scoped invitation issuance, acceptance, and revocation."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.logging import request_id_var
from app.core.security import hash_password
from app.models.billing import BillingPlan, Subscription
from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
from app.models.user import User
from app.models.role import Role
from app.services import audit_service


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def _activate_if_paid(db: AsyncSession, *, invitation: TenantInvitation, user: User) -> bool:
    """Invitation acceptance is not entitlement; activate only after paid Stripe grant."""
    if invitation.accepted_at is None or invitation.revoked_at is not None:
        return False
    paid_subscription = (
        await db.execute(
            select(Subscription.id)
            .join(BillingPlan, BillingPlan.id == Subscription.plan_id)
            .where(
                Subscription.tenant_id == invitation.tenant_id,
                Subscription.status == "active",
                Subscription.provider == "stripe",
                BillingPlan.monthly_price_usd > 0,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if paid_subscription is None:
        return False
    if not user.is_active:
        user.is_active = True
        user.auth_token_version += 1
        await audit_service.record(
            db, action="tenant.invitation_user_activated", actor_type="system",
            tenant_id=invitation.tenant_id, resource_type="user", resource_id=str(user.id),
            request_id=request_id_var.get(), metadata={"grant_source": "stripe_paid_subscription"},
        )
    return True


async def create_invitation(
    db: AsyncSession, *, tenant_id: uuid.UUID, inviter_user_id: uuid.UUID,
    email: str, full_name: str | None, roles: list[Role], expires_in_days: int = 7,
) -> tuple[TenantInvitation, str]:
    """Create an inactive tenant user and issue a hashed, single-use bearer token."""
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id).with_for_update())
    ).scalar_one_or_none()
    if tenant is None or tenant.status != "active":
        raise NotFoundError("Tenant not found or inactive")

    normalized_email = email.strip().lower()
    existing_user = (
        await db.execute(
            select(User).where(User.tenant_id == tenant_id, User.email == normalized_email).with_for_update()
        )
    ).scalar_one_or_none()
    if existing_user is not None:
        prior_for_user = (
            await db.execute(
                select(TenantInvitation).where(
                    TenantInvitation.tenant_id == tenant_id,
                    TenantInvitation.user_id == existing_user.id,
                ).with_for_update()
            )
        ).scalars().all()
        if existing_user.is_active or not prior_for_user or any(row.accepted_at is not None for row in prior_for_user):
            raise ConflictError("A user with this email already exists in the tenant")

    now = datetime.now(timezone.utc)
    previous = (
        await db.execute(
            select(TenantInvitation).where(
                TenantInvitation.tenant_id == tenant_id,
                TenantInvitation.email == normalized_email,
                TenantInvitation.accepted_at.is_(None),
                TenantInvitation.revoked_at.is_(None),
            ).with_for_update()
        )
    ).scalars().all()
    for invitation in previous:
        invitation.revoked_at = now

    # The random placeholder is never disclosed and cannot be used to sign in.
    if existing_user is None:
        user = User(
            tenant_id=tenant_id, email=normalized_email,
            password_hash=hash_password(secrets.token_urlsafe(48)),
            full_name=full_name, is_active=False, is_superuser=False, is_platform_admin=False,
        )
        db.add(user)
    else:
        user = existing_user
        user.full_name = full_name or user.full_name
        user.roles = roles
    if existing_user is None:
        user.roles = roles
    await db.flush()

    raw_token = secrets.token_urlsafe(32)
    invitation = TenantInvitation(
        tenant_id=tenant_id, user_id=user.id, invited_by_user_id=inviter_user_id,
        email=normalized_email, token_hash=_token_hash(raw_token),
        expires_at=now + timedelta(days=expires_in_days),
    )
    db.add(invitation)
    await db.flush()
    await audit_service.record(
        db, action="tenant.invitation_created", actor_type="user", actor_id=inviter_user_id,
        tenant_id=tenant_id, resource_type="tenant_invitation", resource_id=str(invitation.id),
        request_id=request_id_var.get(),
        metadata={"user_id": str(user.id), "email": normalized_email, "expires_at": invitation.expires_at.isoformat(), "role_ids": [str(role.id) for role in roles]},
    )
    return invitation, raw_token


async def accept_invitation(
    db: AsyncSession, *, raw_token: str, password: str,
) -> tuple[TenantInvitation, bool]:
    """Consume a valid invitation once, set credentials, and leave access entitlement-gated."""
    now = datetime.now(timezone.utc)
    invitation = (
        await db.execute(
            select(TenantInvitation).where(TenantInvitation.token_hash == _token_hash(raw_token)).with_for_update()
        )
    ).scalar_one_or_none()
    if (
        invitation is None
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
    ):
        raise UnauthorizedError("Invitation is invalid, expired, revoked, or already used")

    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == invitation.tenant_id))
    ).scalar_one_or_none()
    user = (
        await db.execute(
            select(User).where(
                User.id == invitation.user_id, User.tenant_id == invitation.tenant_id,
                User.email == invitation.email,
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if tenant is None or tenant.status != "active" or user is None:
        raise UnauthorizedError("Invitation is invalid, expired, revoked, or already used")

    invitation.accepted_at = now
    user.password_hash = hash_password(password)
    user.password_changed_at = now
    activated = await _activate_if_paid(db, invitation=invitation, user=user)
    await audit_service.record(
        db, action="tenant.invitation_accepted", actor_type="user", actor_id=user.id,
        tenant_id=invitation.tenant_id, resource_type="tenant_invitation", resource_id=str(invitation.id),
        request_id=request_id_var.get(), metadata={"user_id": str(user.id), "activated": activated},
    )
    return invitation, activated


async def revoke_invitation(
    db: AsyncSession, *, tenant_id: uuid.UUID, invitation_id: uuid.UUID, actor_id: uuid.UUID,
) -> TenantInvitation:
    invitation = (
        await db.execute(
            select(TenantInvitation).where(
                TenantInvitation.id == invitation_id, TenantInvitation.tenant_id == tenant_id,
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if invitation is None:
        raise NotFoundError("Invitation not found")
    if invitation.accepted_at is not None:
        raise ConflictError("Accepted invitation cannot be revoked")
    if invitation.revoked_at is None:
        invitation.revoked_at = datetime.now(timezone.utc)
        await audit_service.record(
            db, action="tenant.invitation_revoked", actor_type="user", actor_id=actor_id,
            tenant_id=tenant_id, resource_type="tenant_invitation", resource_id=str(invitation.id),
            request_id=request_id_var.get(), metadata={"user_id": str(invitation.user_id)},
        )
    return invitation


async def activate_eligible_invited_users(db: AsyncSession, *, tenant_id: uuid.UUID) -> int:
    """Activate only accepted, non-revoked invitees after a paid Stripe grant exists."""
    invitations = (
        await db.execute(
            select(TenantInvitation).where(
                TenantInvitation.tenant_id == tenant_id,
                TenantInvitation.accepted_at.is_not(None),
                TenantInvitation.revoked_at.is_(None),
            ).with_for_update()
        )
    ).scalars().all()
    activated = 0
    for invitation in invitations:
        user = (
            await db.execute(
                select(User).where(
                    User.id == invitation.user_id, User.tenant_id == tenant_id,
                    User.email == invitation.email,
                ).with_for_update()
            )
        ).scalar_one_or_none()
        if user is not None and await _activate_if_paid(db, invitation=invitation, user=user):
            activated += 1
    return activated

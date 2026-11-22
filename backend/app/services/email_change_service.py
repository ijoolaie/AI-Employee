"""Secure, tenant-scoped account email changes with verified ownership."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.logging import request_id_var
from app.core.security import verify_password
from app.models.email_change_token import EmailChangeToken
from app.models.user import User
from app.services import audit_service, outbox_service


def _token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalize_email(email: str) -> str:
    return email.strip().casefold()


async def request_email_change(
    db: AsyncSession, *, user: User, current_password: str, new_email: str,
) -> None:
    locked = (await db.execute(
        select(User).where(User.id == user.id, User.tenant_id == user.tenant_id).with_for_update()
    )).scalar_one_or_none()
    if locked is None or not locked.is_active:
        raise UnauthorizedError("User not found or inactive")
    if not verify_password(current_password, locked.password_hash):
        raise UnauthorizedError("Current password is incorrect")

    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from_email:
        raise ValidationAppError("Email changes are temporarily unavailable because email delivery is not configured")

    normalized = _normalize_email(new_email)
    if normalized == _normalize_email(locked.email):
        raise ConflictError("The new email must be different from the current email")
    conflict = await db.execute(
        select(User.id).where(
            User.tenant_id == locked.tenant_id,
            func.lower(User.email) == normalized,
            User.id != locked.id,
        ).limit(1)
    )
    if conflict.scalar_one_or_none() is not None:
        raise ConflictError("This email address is already in use in this workspace")

    # Pending addresses are reserved within the tenant as well.
    pending_conflict = await db.execute(
        select(User.id).where(
            User.tenant_id == locked.tenant_id,
            func.lower(User.pending_email) == normalized,
            User.id != locked.id,
        ).limit(1)
    )
    if pending_conflict.scalar_one_or_none() is not None:
        raise ConflictError("This email address is already pending verification")

    now = datetime.now(timezone.utc)
    recent_count = (await db.execute(
        select(func.count(EmailChangeToken.id)).where(
            EmailChangeToken.user_id == locked.id,
            EmailChangeToken.created_at >= now - timedelta(hours=1),
        )
    )).scalar_one()
    if recent_count >= 3:
        raise ConflictError("Too many email change requests; try again later")
    latest = (await db.execute(
        select(EmailChangeToken.created_at)
        .where(EmailChangeToken.user_id == locked.id)
        .order_by(EmailChangeToken.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    if latest and latest > now - timedelta(seconds=60):
        raise ConflictError("Please wait before requesting another email change")

    # Retain token history for hourly rate limiting while invalidating older links.
    previous_tokens = list((await db.execute(
        select(EmailChangeToken).where(
            EmailChangeToken.user_id == locked.id,
            EmailChangeToken.used_at.is_(None),
        ).with_for_update()
    )).scalars().all())
    for previous in previous_tokens:
        previous.used_at = now

    raw_token = secrets.token_urlsafe(48)
    token = EmailChangeToken(
        user_id=locked.id,
        tenant_id=locked.tenant_id,
        new_email=normalized,
        token_hash=_token_hash(raw_token),
        expires_at=now + timedelta(minutes=30),
    )
    locked.pending_email = normalized
    db.add(token)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError("This email address is already in use or pending verification") from exc

    confirm_url = f"{settings.frontend_base_url.rstrip('/')}/confirm-email-change?token={raw_token}"
    await outbox_service.enqueue(
        db,
        kind="email.send",
        tenant_id=locked.tenant_id,
        dedupe_key=f"email-change:{token.id}",
        payload={
            "to": [normalized],
            "subject": "Confirm your new AI Employee sign-in email",
            "body": (
                "A request was made to change the sign-in email for your AI Employee account.\n\n"
                f"Confirm the new email within 30 minutes: {confirm_url}\n\n"
                "If you did not request this change, ignore this message. Your current email remains active."
            ),
        },
    )
    await audit_service.record(
        db, action="auth.email_change_requested", actor_type="user",
        actor_id=locked.id, tenant_id=locked.tenant_id,
        request_id=request_id_var.get(),
        metadata={"previous_email": locked.email, "pending_email": normalized},
    )
    await db.flush()


async def confirm_email_change(db: AsyncSession, *, raw_token: str) -> None:
    now = datetime.now(timezone.utc)
    token_hash = _token_hash(raw_token)
    probe = (await db.execute(
        select(EmailChangeToken).where(EmailChangeToken.token_hash == token_hash)
    )).scalar_one_or_none()
    if probe is None or probe.used_at is not None or probe.expires_at <= now:
        raise UnauthorizedError("Invalid or expired email verification link")

    # Lock in canonical parent -> child order, then re-read the token under lock.
    user = (await db.execute(
        select(User).where(
            User.id == probe.user_id, User.tenant_id == probe.tenant_id
        ).with_for_update()
    )).scalar_one_or_none()
    if user is None or not user.is_active or user.pending_email is None:
        raise UnauthorizedError("Invalid or expired email verification link")
    token = (await db.execute(
        select(EmailChangeToken).where(
            EmailChangeToken.id == probe.id,
            EmailChangeToken.user_id == user.id,
            EmailChangeToken.tenant_id == user.tenant_id,
            EmailChangeToken.token_hash == token_hash,
        ).with_for_update()
    )).scalar_one_or_none()
    if (
        token is None or token.used_at is not None or token.expires_at <= now
        or _normalize_email(user.pending_email) != token.new_email
    ):
        raise UnauthorizedError("Invalid or expired email verification link")

    # Database uniqueness is the final race-safe guard.
    user.email = token.new_email
    user.pending_email = None
    user.auth_token_version += 1
    token.used_at = now
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError("This email address is already in use in this workspace") from exc

    await audit_service.record(
        db, action="auth.email_change_completed", actor_type="user",
        actor_id=user.id, tenant_id=user.tenant_id,
        request_id=request_id_var.get(),
        metadata={"new_email": user.email, "sessions_invalidated": True},
    )
    await db.flush()
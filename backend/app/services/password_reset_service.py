"""Secure, tenant-scoped password recovery using single-use hashed tokens."""
from __future__ import annotations
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.logging import request_id_var
from app.core.security import hash_password
from app.models.password_reset_token import PasswordResetToken
from app.models.tenant import Tenant
from app.models.user import User
from app.services import audit_service, outbox_service

GENERIC_MESSAGE = "If the account exists, a password reset email has been sent."

def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

async def request_reset(db: AsyncSession, *, email: str, tenant_slug: str) -> str:
    settings = get_settings()
    tenant_result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None or tenant.status != "active":
        return GENERIC_MESSAGE
    normalized = email.lower()
    user_result = await db.execute(select(User).where(User.email == normalized, User.tenant_id == tenant.id, User.is_active.is_(True)))
    user = user_result.scalar_one_or_none()
    if user is None:
        return GENERIC_MESSAGE

    since = datetime.now(timezone.utc) - timedelta(minutes=settings.password_reset_rate_window_minutes)
    count_result = await db.execute(select(func.count(PasswordResetToken.id)).where(PasswordResetToken.user_id == user.id, PasswordResetToken.created_at >= since))
    if int(count_result.scalar_one() or 0) >= settings.password_reset_rate_limit:
        return GENERIC_MESSAGE

    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)))
    raw_token = secrets.token_urlsafe(48)
    token = PasswordResetToken(user_id=user.id, tenant_id=tenant.id, token_hash=_hash(raw_token), expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_expire_minutes))
    db.add(token)
    await db.flush()
    reset_url = f"{settings.frontend_base_url.rstrip('/')}/reset-password?token={raw_token}"
    body = (f"Hello {user.full_name or 'there'},\n\n"
            "We received a request to reset your AI Employee Platform password.\n\n"
            f"Reset your password here (valid for {settings.password_reset_token_expire_minutes} minutes):\n{reset_url}\n\n"
            "This link can only be used once. If you did not request this, you can safely ignore this email.\n")
    await outbox_service.enqueue(db, kind="email.send", tenant_id=tenant.id,
        dedupe_key=f"password-reset:{token.id}",
        payload={"to": [user.email], "subject": "Reset your AI Employee Platform password", "body": body})
    await audit_service.record(db, action="auth.password_reset_requested", actor_type="user", actor_id=user.id, tenant_id=tenant.id, request_id=request_id_var.get(), metadata={})
    return GENERIC_MESSAGE

async def reset_password(db: AsyncSession, *, raw_token: str, password: str) -> None:
    now = datetime.now(timezone.utc)
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash(raw_token)).with_for_update())
    token = result.scalar_one_or_none()
    if token is None or token.used_at is not None or token.expires_at <= now:
        raise UnauthorizedError("Invalid or expired password reset token")
    user_result = await db.execute(select(User).where(User.id == token.user_id, User.tenant_id == token.tenant_id).with_for_update())
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or expired password reset token")
    user.password_hash = hash_password(password)
    user.password_changed_at = now
    user.auth_token_version += 1
    token.used_at = now
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.id != token.id))
    await audit_service.record(db, action="auth.password_reset_completed", actor_type="user", actor_id=user.id, tenant_id=user.tenant_id, request_id=request_id_var.get(), metadata={})
    await db.flush()

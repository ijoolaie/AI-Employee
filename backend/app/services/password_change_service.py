"""Authenticated password change service."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.logging import request_id_var
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.services import audit_service


async def change_password(
    db: AsyncSession,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """Change the authenticated user's password and invalidate all sessions."""
    result = await db.execute(
        select(User).where(User.id == user.id, User.tenant_id == user.tenant_id).with_for_update()
    )
    locked_user = result.scalar_one_or_none()
    if locked_user is None or not locked_user.is_active:
        raise UnauthorizedError("User not found or inactive")

    if not verify_password(current_password, locked_user.password_hash):
        raise UnauthorizedError("Current password is incorrect")

    if verify_password(new_password, locked_user.password_hash):
        raise UnauthorizedError("New password must be different from the current password")

    now = datetime.now(timezone.utc)
    locked_user.password_hash = hash_password(new_password)
    locked_user.password_changed_at = now
    locked_user.auth_token_version += 1

    await audit_service.record(
        db,
        action="auth.password_changed",
        actor_type="user",
        actor_id=locked_user.id,
        tenant_id=locked_user.tenant_id,
        request_id=request_id_var.get(),
        metadata={},
    )
    await db.flush()

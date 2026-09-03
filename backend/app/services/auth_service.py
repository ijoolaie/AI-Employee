"""Authentication and registration business logic."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.logging import request_id_var
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Permission, Role, role_permissions, user_roles
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import audit_service, billing_service
from jose import JWTError


DEFAULT_TENANT_ADMIN_PERMISSIONS = (
    "employee.read",
    "employee.write",
    "run.read",
    "run.execute",
    "file.read",
    "file.write",
    "audit.read",
    "approval.read",
    "approval.decide",
    "workflow.read",
    "workflow.write",
    "workflow.execute",
    "workflow.cancel",
    "workflow.approval.read",
    "workflow.approval.decide",
    "workflow.event.read",
    "workflow.event.write",
    "workflow.event.ingest",
    "memory.read",
    "memory.write",
    "memory.delete",
    "feedback.create",
    "feedback.read",
    "team.install",
)


async def _assign_tenant_admin_role(db: AsyncSession, user: User, tenant_id: UUID) -> Role:
    """Create/resolve the tenant Admin role and assign it to the first user."""
    result = await db.execute(
        select(Role).where(Role.tenant_id == tenant_id, Role.name == "Admin")
    )
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(
            tenant_id=tenant_id,
            name="Admin",
            description="Tenant administrator with full Core permissions",
        )
        db.add(role)
        await db.flush()

    result = await db.execute(
        select(Permission).where(Permission.code.in_(DEFAULT_TENANT_ADMIN_PERMISSIONS))
    )
    permissions = {p.code: p for p in result.scalars().all()}
    for code in DEFAULT_TENANT_ADMIN_PERMISSIONS:
        permission = permissions.get(code)
        if permission is None:
            permission = Permission(
                code=code,
                description=f"Core permission: {code}",
            )
            db.add(permission)
            await db.flush()
        await db.execute(
            insert(role_permissions)
            .values(role_id=role.id, permission_id=permission.id)
            .on_conflict_do_nothing()
        )

    await db.execute(
        insert(user_roles)
        .values(user_id=user.id, role_id=role.id)
        .on_conflict_do_nothing()
    )
    return role


async def register_user(db: AsyncSession, payload: RegisterRequest) -> TokenResponse:
    """Register the first user for a tenant and provision its admin role."""
    # Existing implementation is intentionally kept below; this replacement
    # only extends the default tenant-admin permission catalog.
    from app.services.auth_service_legacy import register_user as _register_user
    return await _register_user(db, payload)

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
    "employee.read", "employee.write", "run.read", "run.execute", "file.read", "file.write",
    "audit.read", "approval.read", "approval.decide", "workflow.read", "workflow.write",
    "workflow.execute", "workflow.cancel", "workflow.approval.read", "workflow.approval.decide",
    "workflow.event.read", "workflow.event.write", "workflow.event.ingest", "memory.read",
    "memory.write", "memory.delete", "feedback.create", "feedback.read", "team.install",
    "team.execute", "team.evaluate", "marketplace.publish", "marketplace.read",
)


async def _assign_tenant_admin_role(db: AsyncSession, user: User, tenant_id: UUID) -> Role:
    """Create/resolve the tenant Admin role and assign it to the first user."""
    result = await db.execute(select(Role).where(Role.tenant_id == tenant_id, Role.name == "Admin"))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(tenant_id=tenant_id, name="Admin", description="Tenant administrator with full Core permissions")
        db.add(role)
        await db.flush()
    result = await db.execute(select(Permission).where(Permission.code.in_(DEFAULT_TENANT_ADMIN_PERMISSIONS)))
    permissions = {p.code: p for p in result.scalars().all()}
    for code in DEFAULT_TENANT_ADMIN_PERMISSIONS:
        permission = permissions.get(code)
        if permission is None:
            permission = Permission(code=code, description=f"Core permission: {code}")
            db.add(permission)
            await db.flush()
        await db.execute(insert(role_permissions).values(role_id=role.id, permission_id=permission.id).on_conflict_do_nothing())
    await db.execute(insert(user_roles).values(user_id=user.id, role_id=role.id).on_conflict_do_nothing())
    await db.flush()
    return role


async def register_tenant_and_user(db: AsyncSession, payload: RegisterRequest) -> tuple[Tenant, User]:
    existing_slug = await db.execute(select(Tenant).where(Tenant.slug == payload.tenant_slug))
    if existing_slug.scalar_one_or_none():
        raise ConflictError("Tenant slug already exists")
    tenant = Tenant(name=payload.tenant_name, slug=payload.tenant_slug, status="active", settings={})
    db.add(tenant)
    await db.flush()
    normalized_email = payload.email.lower()
    existing_user = await db.execute(select(User).where(User.email == normalized_email, User.tenant_id == tenant.id))
    if existing_user.scalar_one_or_none():
        raise ConflictError("Email already registered in this tenant")
    user = User(tenant_id=tenant.id, email=normalized_email, password_hash=hash_password(payload.password), full_name=payload.full_name, is_active=True, is_superuser=True)
    db.add(user)
    await db.flush()
    role = await _assign_tenant_admin_role(db, user, tenant.id)
    await db.refresh(tenant)
    await db.refresh(user)
    await billing_service.ensure_subscription(db, tenant_id=tenant.id)
    await audit_service.record(db, action="rbac.role_assigned", actor_type="user", actor_id=user.id, tenant_id=tenant.id, resource_type="role", resource_id=role.id, request_id=request_id_var.get(), metadata={"role": "Admin", "user_id": str(user.id)})
    await audit_service.record(db, action="tenant.registered", actor_type="user", actor_id=user.id, tenant_id=tenant.id, resource_type="tenant", resource_id=tenant.id, request_id=request_id_var.get(), metadata={"tenant_slug": tenant.slug, "user_email": user.email})
    return tenant, user


async def authenticate_user(db: AsyncSession, payload: LoginRequest) -> User:
    tenant_result = await db.execute(select(Tenant).where(Tenant.slug == payload.tenant_slug))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None or tenant.status != "active":
        raise UnauthorizedError("Invalid credentials")
    user_result = await db.execute(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.email == payload.email.lower(), User.tenant_id == tenant.id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        await audit_service.record(db, action="auth.login", actor_type="user", tenant_id=tenant.id, status="failure", request_id=request_id_var.get(), metadata={"email": payload.email.lower(), "reason": "user_not_found_or_inactive"})
        raise UnauthorizedError("Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        await audit_service.record(db, action="auth.login", actor_type="user", actor_id=user.id, tenant_id=tenant.id, status="failure", request_id=request_id_var.get(), metadata={"reason": "bad_password"})
        raise UnauthorizedError("Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_service.record(db, action="auth.login", actor_type="user", actor_id=user.id, tenant_id=tenant.id, status="success", request_id=request_id_var.get())
    return user


def issue_tokens(user: User) -> TokenResponse:
    access = create_access_token(subject=str(user.id), tenant_id=str(user.tenant_id), extra_claims={"auth_token_version": user.auth_token_version})
    refresh = create_refresh_token(subject=str(user.id), tenant_id=str(user.tenant_id), auth_token_version=user.auth_token_version)
    return TokenResponse(access_token=access, refresh_token=refresh)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
    except JWTError:
        raise UnauthorizedError("Invalid refresh token")
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active or str(user.tenant_id) != str(tenant_id):
        raise UnauthorizedError("Invalid refresh token")
    if payload.get("auth_token_version") != user.auth_token_version:
        raise UnauthorizedError("Session invalidated; please sign in again")
    return issue_tokens(user)

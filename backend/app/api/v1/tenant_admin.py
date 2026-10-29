"""Tenant administration: users and roles, strictly tenant-scoped."""
import re
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.deps import CurrentContext, DbSession
from app.models.user import User
from app.models.role import Role
from app.models.tenant import Tenant
from app.schemas.common import APIResponse
from app.services import audit_service

router = APIRouter(prefix="/tenant-admin", tags=["tenant-admin"])

class UserSummary(BaseModel):
    id: UUID; email: str; full_name: str | None; is_active: bool; roles: list[str]
class RoleSummary(BaseModel):
    id: UUID; name: str; description: str | None; permissions: list[str]
class UserStatusUpdate(BaseModel):
    is_active: bool
class UserRolesUpdate(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list)

class HandoffNotificationSettingsUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=320)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("A valid notification email address is required")
        return normalized

class HandoffNotificationSettings(BaseModel):
    email: str | None = None

async def require_tenant_admin(ctx: CurrentContext):
    if not ctx.user.is_superuser and not any(r.name.lower() in {"admin", "owner", "tenant_admin"} and r.tenant_id == ctx.tenant_id for r in ctx.user.roles):
        raise HTTPException(status_code=403, detail="Tenant administrator access required")
    return ctx


def _effective_permission_codes(ctx: CurrentContext) -> set[str]:
    if ctx.user.is_superuser:
        return set()
    return {
        permission.code
        for role in ctx.user.roles
        if role.tenant_id == ctx.tenant_id
        for permission in role.permissions
    }


def _assert_roles_within_authority(ctx: CurrentContext, roles: list[Role]) -> None:
    """Reject any role set that would grant permissions the actor lacks."""
    if ctx.user.is_superuser:
        return
    actor_permissions = _effective_permission_codes(ctx)
    requested_permissions = {permission.code for role in roles for permission in role.permissions}
    if not requested_permissions.issubset(actor_permissions):
        raise HTTPException(status_code=403, detail="Cannot assign roles with permissions exceeding your authority")


async def _load_assignable_roles(payload: UserRolesUpdate, ctx: CurrentContext, db: DbSession) -> list[Role]:
    roles_result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).where(
            Role.id.in_(payload.role_ids),
            ((Role.tenant_id == ctx.tenant_id) | (Role.tenant_id.is_(None))),
        )
    )
    roles = roles_result.scalars().all()
    if len(roles) != len(set(payload.role_ids)):
        raise HTTPException(status_code=400, detail="One or more roles are invalid for this tenant")
    _assert_roles_within_authority(ctx, roles)
    return roles


@router.get("/customer-handoff-notification", response_model=APIResponse[HandoffNotificationSettings])
async def get_customer_handoff_notification(ctx: CurrentContext, db: DbSession):
    """Read the authenticated tenant's private handoff notification destination."""
    await require_tenant_admin(ctx)
    result = await db.execute(select(Tenant.settings).where(Tenant.id == ctx.tenant_id))
    settings = result.scalar_one_or_none() or {}
    email = settings.get("customer_handoff_notification_email") if isinstance(settings, dict) else None
    return APIResponse(success=True, data=HandoffNotificationSettings(email=email))


@router.put("/customer-handoff-notification", response_model=APIResponse[HandoffNotificationSettings])
async def update_customer_handoff_notification(payload: HandoffNotificationSettingsUpdate, ctx: CurrentContext, db: DbSession):
    """Set or clear this tenant's staff notification email; never expose provider secrets."""
    await require_tenant_admin(ctx)
    result = await db.execute(select(Tenant).where(Tenant.id == ctx.tenant_id).with_for_update())
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    email = payload.validate_email(payload.email)
    settings = dict(tenant.settings or {})
    if email:
        settings["customer_handoff_notification_email"] = email
    else:
        settings.pop("customer_handoff_notification_email", None)
    tenant.settings = settings
    await audit_service.record(
        db,
        action="tenant.customer_handoff_notification_updated",
        actor_type="user",
        actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        resource_type="tenant_settings",
        resource_id=str(ctx.tenant_id),
        metadata={"configured": bool(email)},
    )
    await db.commit()
    return APIResponse(success=True, data=HandoffNotificationSettings(email=email))

@router.get("/users", response_model=APIResponse[list[UserSummary]])
async def list_users(ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.tenant_id == ctx.tenant_id).order_by(User.created_at))
    rows = result.scalars().all()
    return APIResponse(success=True, data=[UserSummary(id=u.id,email=u.email,full_name=u.full_name,is_active=u.is_active,roles=[r.name for r in u.roles if r.tenant_id == ctx.tenant_id]) for u in rows])

@router.get("/roles", response_model=APIResponse[list[RoleSummary]])
async def list_roles(ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    result = await db.execute(select(Role).options(selectinload(Role.permissions)).where((Role.tenant_id == ctx.tenant_id) | (Role.tenant_id.is_(None))).order_by(Role.name))
    rows = result.scalars().all()
    return APIResponse(success=True, data=[RoleSummary(id=r.id,name=r.name,description=r.description,permissions=[p.code for p in r.permissions]) for r in rows])

@router.post("/users/{user_id}/status", response_model=APIResponse[UserSummary])
async def update_user_status(user_id: UUID, payload: UserStatusUpdate, ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    if user_id == ctx.user_id and not payload.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id, User.tenant_id == ctx.tenant_id).with_for_update())
    user = result.scalar_one_or_none()
    if user is None: raise HTTPException(status_code=404, detail="User not found")
    user.is_active = payload.is_active
    await audit_service.record(db, action="tenant.user_status_updated", actor_type="user", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="user", resource_id=str(user.id), metadata={"is_active": payload.is_active})
    await db.commit(); await db.refresh(user)
    return APIResponse(success=True, data=UserSummary(id=user.id,email=user.email,full_name=user.full_name,is_active=user.is_active,roles=[r.name for r in user.roles if r.tenant_id == ctx.tenant_id]))

@router.post("/users/{user_id}/roles", response_model=APIResponse[UserSummary])
async def update_user_roles(user_id: UUID, payload: UserRolesUpdate, ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id, User.tenant_id == ctx.tenant_id).with_for_update())
    user = result.scalar_one_or_none()
    if user is None: raise HTTPException(status_code=404, detail="User not found")
    roles = await _load_assignable_roles(payload, ctx, db)
    user.roles = roles
    await audit_service.record(db, action="tenant.user_roles_updated", actor_type="user", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="user", resource_id=str(user.id), metadata={"role_ids": [str(role.id) for role in roles]})
    await db.commit(); await db.refresh(user)
    return APIResponse(success=True, data=UserSummary(id=user.id,email=user.email,full_name=user.full_name,is_active=user.is_active,roles=[r.name for r in user.roles if r.tenant_id == ctx.tenant_id]))

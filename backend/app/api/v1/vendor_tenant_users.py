"""Vendor administration of tenant-local users in the vendor's persisted subtree."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession
from app.core.edition_deps import VendorAdminContext, _has_action_permission
from app.models.role import Role, user_roles
from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.edition import TenantInvitationResponse, TenantInvitationRevokedResponse
from app.services import audit_service, tenant_access_service, tenant_invitation_service
from app.services.edition_service import EDITION_RESELLER
from app.services.tenant_user_management_service import resolve_user_management_target
from app.api.v1.tenant_admin import _assert_roles_within_authority

router = APIRouter(prefix="/edition/vendor/tenants/{target_tenant_id}/users", tags=["vendor-tenant-users"])
ADMIN_ROLE_NAMES = {"admin", "owner", "tenant_admin"}


class VendorManagedUserSummary(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    roles: list[str]


class VendorManagedRoleSummary(BaseModel):
    id: UUID
    name: str
    description: str | None
    permissions: list[str]


class VendorUserInvitationRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    expires_in_days: int = Field(default=7, ge=1, le=30)


class VendorUserStatusRequest(BaseModel):
    is_active: bool


class VendorUserRolesRequest(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list)


def _assert_vendor_assignable_roles(ctx: VendorAdminContext, roles: list[Role]) -> None:
    if any(role.name.strip().lower().replace(" ", "_") in {"superuser", "platform_admin", "platform_superuser"} for role in roles):
        raise HTTPException(status_code=403, detail="Platform administrator roles cannot be delegated")
    permission_codes = {permission.code for role in roles for permission in role.permissions}
    if any(code.startswith(("vendor.", "platform.")) for code in permission_codes):
        raise HTTPException(status_code=403, detail="Platform and Vendor control-plane permissions cannot be delegated")
    _assert_roles_within_authority(ctx, roles)


async def _resolve_target_and_authorize(ctx: VendorAdminContext, db: DbSession, target_tenant_id: UUID, *, write: bool = False):
    target = await resolve_user_management_target(db, actor_tenant_id=ctx.tenant_id, target_tenant_id=target_tenant_id)
    if target.tenant_kind == EDITION_RESELLER:
        permission = "vendor.reseller.manage" if write else "vendor.reseller.read"
    else:
        permission = "vendor.customer.manage" if write else "vendor.customer.read"
    if not await _has_action_permission(ctx, db, permission):
        raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
    return target


async def _refresh_vendor_actor(ctx: VendorAdminContext, db: DbSession) -> None:
    # Re-read and lock the actor after the target lock so concurrent role
    # revocation/deactivation cannot leave this mutation using stale authority.
    actor = (await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == ctx.user_id, User.tenant_id == ctx.tenant_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )).scalar_one_or_none()
    if actor is None or not actor.is_active:
        raise HTTPException(status_code=401, detail="Vendor actor not found or inactive")
    ctx.user = actor


async def _lock_target_and_authorize(ctx: VendorAdminContext, db: DbSession, target_tenant_id: UUID):
    # Serialize child-user lifecycle operations with tenant lifecycle and each other.
    locked = (await db.execute(select(Tenant).where(Tenant.id == target_tenant_id).with_for_update())).scalar_one_or_none()
    if locked is None:
        raise HTTPException(status_code=404, detail="Target tenant not found")
    await _refresh_vendor_actor(ctx, db)
    return await _resolve_target_and_authorize(ctx, db, target_tenant_id, write=True)


async def _record_vendor_change(db: DbSession, *, ctx: VendorAdminContext, target: Tenant, action: str, resource_type: str, resource_id: UUID, metadata: dict):
    details = {"actor_tenant_id": str(ctx.tenant_id), "target_tenant_id": str(target.id), **metadata}
    await audit_service.record(
        db, action=action, actor_type="user", actor_id=ctx.user_id,
        tenant_id=target.id, resource_type=resource_type, resource_id=str(resource_id), metadata=details,
    )
    await audit_service.record(
        db, action=f"vendor.{target.tenant_kind}.{action.split('.')[-1]}",
        actor_type="user", actor_id=ctx.user_id, tenant_id=ctx.tenant_id,
        resource_type=resource_type, resource_id=str(resource_id), metadata=details,
    )


@router.get("", response_model=APIResponse[list[VendorManagedUserSummary]])
async def list_vendor_managed_users(target_tenant_id: UUID, ctx: VendorAdminContext, db: DbSession):
    target = await _resolve_target_and_authorize(ctx, db, target_tenant_id)
    rows = (await db.execute(select(User).options(selectinload(User.roles)).where(User.tenant_id == target.id).order_by(User.created_at))).scalars().all()
    return APIResponse(success=True, data=[VendorManagedUserSummary(id=user.id, email=user.email, full_name=user.full_name, is_active=user.is_active, roles=[role.name for role in user.roles if role.tenant_id == target.id]) for user in rows])


@router.get("/roles", response_model=APIResponse[list[VendorManagedRoleSummary]])
async def list_vendor_managed_roles(target_tenant_id: UUID, ctx: VendorAdminContext, db: DbSession):
    target = await _resolve_target_and_authorize(ctx, db, target_tenant_id)
    rows = (await db.execute(select(Role).options(selectinload(Role.permissions)).where((Role.tenant_id == target.id) | (Role.tenant_id.is_(None))).order_by(Role.name))).scalars().all()
    return APIResponse(success=True, data=[VendorManagedRoleSummary(id=role.id, name=role.name, description=role.description, permissions=[permission.code for permission in role.permissions]) for role in rows])


@router.post("/invitations", response_model=APIResponse[TenantInvitationResponse], status_code=201)
async def invite_vendor_managed_user(target_tenant_id: UUID, payload: VendorUserInvitationRequest, ctx: VendorAdminContext, db: DbSession):
    target = await _lock_target_and_authorize(ctx, db, target_tenant_id)
    invitation, raw_token = await tenant_invitation_service.create_invitation(
        db, tenant_id=target.id, inviter_user_id=ctx.user_id, email=str(payload.email),
        full_name=payload.full_name, roles=[], expires_in_days=payload.expires_in_days,
    )
    await _record_vendor_change(db, ctx=ctx, target=target, action="vendor_user.invitation_created", resource_type="tenant_invitation", resource_id=invitation.id, metadata={"target_user_id": str(invitation.user_id), "email": invitation.email})
    return APIResponse(success=True, data=TenantInvitationResponse(id=invitation.id, user_id=invitation.user_id, email=invitation.email, token=raw_token, expires_at=invitation.expires_at))


@router.post("/invitations/{invitation_id}/revoke", response_model=APIResponse[TenantInvitationRevokedResponse])
async def revoke_vendor_managed_invitation(target_tenant_id: UUID, invitation_id: UUID, ctx: VendorAdminContext, db: DbSession):
    target = await _lock_target_and_authorize(ctx, db, target_tenant_id)
    invitation = await tenant_invitation_service.revoke_invitation(db, tenant_id=target.id, invitation_id=invitation_id, actor_id=ctx.user_id)
    await _record_vendor_change(db, ctx=ctx, target=target, action="vendor_user.invitation_revoked", resource_type="tenant_invitation", resource_id=invitation.id, metadata={"target_user_id": str(invitation.user_id)})
    return APIResponse(success=True, data=TenantInvitationRevokedResponse(id=invitation.id, revoked_at=invitation.revoked_at))


@router.post("/{user_id}/status", response_model=APIResponse[VendorManagedUserSummary])
async def update_vendor_managed_user_status(target_tenant_id: UUID, user_id: UUID, payload: VendorUserStatusRequest, ctx: VendorAdminContext, db: DbSession):
    target = await _lock_target_and_authorize(ctx, db, target_tenant_id)
    user = (await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id, User.tenant_id == target.id).with_for_update())).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Target-tenant user not found")
    if user.is_active and not payload.is_active and any(role.tenant_id == target.id and role.name.lower() in ADMIN_ROLE_NAMES for role in user.roles):
        active_admin_count = (await db.execute(
            select(func.count(func.distinct(User.id))).select_from(User)
            .join(user_roles, user_roles.c.user_id == User.id).join(Role, Role.id == user_roles.c.role_id)
            .where(User.tenant_id == target.id, User.is_active.is_(True), Role.tenant_id == target.id, func.lower(Role.name).in_(ADMIN_ROLE_NAMES))
        )).scalar_one()
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="Cannot deactivate the last active target-tenant administrator")
    if not user.is_active and payload.is_active:
        accepted = (await db.execute(select(TenantInvitation.id).where(
            TenantInvitation.user_id == user.id, TenantInvitation.tenant_id == target.id,
            TenantInvitation.accepted_at.is_not(None), TenantInvitation.revoked_at.is_(None),
        ).limit(1))).scalar_one_or_none()
        if accepted is None:
            raise HTTPException(status_code=409, detail="Target-tenant users must accept an invitation before activation")
        if not await tenant_access_service.tenant_has_access(db, tenant=target):
            raise HTTPException(status_code=402, detail="Target tenant requires paid or active Demo entitlement")
    if user.is_active != payload.is_active:
        user.is_active = payload.is_active
        user.auth_token_version += 1
        await _record_vendor_change(db, ctx=ctx, target=target, action="vendor_user.status_updated", resource_type="user", resource_id=user.id, metadata={"is_active": payload.is_active, "before_is_active": not payload.is_active})
        await db.flush()
    return APIResponse(success=True, data=VendorManagedUserSummary(id=user.id, email=user.email, full_name=user.full_name, is_active=user.is_active, roles=[role.name for role in user.roles if role.tenant_id == target.id]))

@router.post("/{user_id}/roles", response_model=APIResponse[VendorManagedUserSummary])
async def update_vendor_managed_user_roles(target_tenant_id: UUID, user_id: UUID, payload: VendorUserRolesRequest, ctx: VendorAdminContext, db: DbSession):
    target = await _lock_target_and_authorize(ctx, db, target_tenant_id)
    user = (await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id, User.tenant_id == target.id).with_for_update())).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Target-tenant user not found")
    if len(payload.role_ids) != len(set(payload.role_ids)):
        raise HTTPException(status_code=400, detail="Duplicate role IDs are not allowed")
    roles = (await db.execute(select(Role).options(selectinload(Role.permissions)).where(
        Role.id.in_(payload.role_ids), ((Role.tenant_id == target.id) | (Role.tenant_id.is_(None)))
    ))).scalars().all() if payload.role_ids else []
    if len(roles) != len(payload.role_ids):
        raise HTTPException(status_code=400, detail="One or more roles are invalid for this target tenant")
    # Reuse tenant-admin delegation ceiling: only explicitly held permissions
    # can be delegated; vendor control-plane permissions are never delegable.
    _assert_vendor_assignable_roles(ctx, roles)
    before_role_ids = {role.id for role in user.roles if role.tenant_id == target.id}
    before_is_admin = user.is_active and any(role.tenant_id == target.id and role.name.lower() in ADMIN_ROLE_NAMES for role in user.roles)
    after_is_admin = any(role.tenant_id == target.id and role.name.lower() in ADMIN_ROLE_NAMES for role in roles)
    if before_is_admin and not after_is_admin:
        active_admin_count = (await db.execute(
            select(func.count(func.distinct(User.id))).select_from(User)
            .join(user_roles, user_roles.c.user_id == User.id).join(Role, Role.id == user_roles.c.role_id)
            .where(User.tenant_id == target.id, User.is_active.is_(True), Role.tenant_id == target.id, func.lower(Role.name).in_(ADMIN_ROLE_NAMES))
        )).scalar_one()
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="Cannot remove the last active target-tenant administrator")
    # Preserve only target-local assignments; system roles are intentionally
    # allowed only when their permissions remain within the actor's authority.
    foreign_roles = [role for role in user.roles if role.tenant_id != target.id]
    user.roles = foreign_roles + roles
    after_role_ids = [str(role.id) for role in roles]
    if before_role_ids != {role.id for role in roles}:
        await _record_vendor_change(db, ctx=ctx, target=target, action="vendor_user.roles_updated", resource_type="user", resource_id=user.id, metadata={"before_role_ids": sorted(str(value) for value in before_role_ids), "role_ids": after_role_ids})
        await db.flush()
    return APIResponse(success=True, data=VendorManagedUserSummary(id=user.id, email=user.email, full_name=user.full_name, is_active=user.is_active, roles=[role.name for role in user.roles if role.tenant_id == target.id]))

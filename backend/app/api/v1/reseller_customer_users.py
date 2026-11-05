"""Reseller-scoped management of users in directly owned Customer tenants."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession
from app.core.edition_deps import ResellerCustomerManageContext
from app.models.role import Permission, Role, user_roles
from app.models.tenant import Tenant
from app.models.user import User
from app.models.tenant_invitation import TenantInvitation
from app.schemas.common import APIResponse
from app.schemas.edition import TenantInvitationResponse, TenantInvitationRevokedResponse
from app.services import audit_service, edition_service, tenant_access_service, tenant_invitation_service

router = APIRouter(prefix="/edition/reseller/customers/{customer_id}/users", tags=["reseller-customer-users"])

CUSTOMER_MEMBER_PERMISSIONS = frozenset({
    "employee.read",
    "employee.write",
    "run.read",
    "run.execute",
    "file.read",
    "file.write",
    "workflow.read",
    "workflow.execute",
    "memory.read",
    "memory.write",
    "feedback.create",
    "feedback.read",
    "team.install",
    "team.execute",
    "team.evaluate",
    "marketplace.read",
    "marketplace.install",
    "skill_marketplace.purchase",
    "employee_marketplace.install",
})


class CustomerUserInvitationRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    expires_in_days: int = Field(default=7, ge=1, le=30)


class CustomerUserStatusRequest(BaseModel):
    is_active: bool


class CustomerUserSummary(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    roles: list[str]


async def _load_direct_customer(customer_id: UUID, ctx, db: DbSession, *, lock: bool = False) -> Tenant:
    query = select(Tenant).where(Tenant.id == customer_id)
    if lock:
        query = query.with_for_update()
    customer = (await db.execute(query)).scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    edition_service.assert_direct_child(ctx.tenant, customer, edition_service.EDITION_CUSTOMER)
    if customer.status != "active":
        raise HTTPException(status_code=403, detail="Customer tenant is inactive")
    return customer


async def _customer_member_role(db: DbSession, customer: Tenant) -> Role:
    role = (await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.tenant_id == customer.id, Role.name == "Reseller Managed Member")
        .with_for_update()
    )).scalar_one_or_none()
    if role is not None:
        existing_codes = {permission.code for permission in role.permissions}
        if existing_codes != CUSTOMER_MEMBER_PERMISSIONS:
            raise HTTPException(status_code=409, detail="Customer member role differs from the approved least-privilege policy")
        return role

    permissions = (await db.execute(
        select(Permission).where(Permission.code.in_(CUSTOMER_MEMBER_PERMISSIONS))
    )).scalars().all()
    found_codes = {permission.code for permission in permissions}
    for code in CUSTOMER_MEMBER_PERMISSIONS - found_codes:
        permission = Permission(code=code, description="Least-privilege Reseller-managed Customer member access")
        db.add(permission)
        permissions.append(permission)
    role = Role(
        tenant_id=customer.id,
        name="Reseller Managed Member",
        description="Least-privilege role for additional users invited by the owning Reseller",
    )
    role.permissions = permissions
    db.add(role)
    await db.flush()
    return role


@router.get("", response_model=APIResponse[list[CustomerUserSummary]])
async def list_customer_users(customer_id: UUID, ctx: ResellerCustomerManageContext, db: DbSession):
    customer = await _load_direct_customer(customer_id, ctx, db)
    rows = (await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.tenant_id == customer.id)
        .order_by(User.created_at)
    )).scalars().all()
    return APIResponse(success=True, data=[
        CustomerUserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=[role.name for role in user.roles if role.tenant_id == customer.id],
        )
        for user in rows
    ])


@router.post("/invitations", response_model=APIResponse[TenantInvitationResponse], status_code=201)
async def invite_customer_user(
    customer_id: UUID,
    payload: CustomerUserInvitationRequest,
    ctx: ResellerCustomerManageContext,
    db: DbSession,
):
    customer = await _load_direct_customer(customer_id, ctx, db, lock=True)
    existing_user = (await db.execute(
        select(User.id).where(
            User.tenant_id == customer.id,
            func.lower(User.email) == str(payload.email).lower(),
        ).limit(1)
    )).scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="A user with this email already exists in the Customer tenant")
    member_role = await _customer_member_role(db, customer)
    invitation, raw_token = await tenant_invitation_service.create_invitation(
        db,
        tenant_id=customer.id,
        inviter_user_id=ctx.user_id,
        email=str(payload.email),
        full_name=payload.full_name,
        roles=[member_role],
        expires_in_days=payload.expires_in_days,
    )
    await audit_service.record(
        db,
        action="reseller.customer_user.invitation_created",
        actor_type="user",
        actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        resource_type="tenant_invitation",
        resource_id=str(invitation.id),
        metadata={
            "actor_tenant_id": str(ctx.tenant_id),
            "target_tenant_id": str(customer.id),
            "target_user_id": str(invitation.user_id),
            "email": invitation.email,
            "role": member_role.name,
        },
    )
    return APIResponse(success=True, data=TenantInvitationResponse(
        id=invitation.id,
        user_id=invitation.user_id,
        email=invitation.email,
        token=raw_token,
        expires_at=invitation.expires_at,
    ))


@router.post("/invitations/{invitation_id}/revoke", response_model=APIResponse[TenantInvitationRevokedResponse])
async def revoke_customer_user_invitation(
    customer_id: UUID,
    invitation_id: UUID,
    ctx: ResellerCustomerManageContext,
    db: DbSession,
):
    customer = await _load_direct_customer(customer_id, ctx, db, lock=True)
    owned_invitation = (await db.execute(
        select(tenant_invitation_service.TenantInvitation.id).where(
            tenant_invitation_service.TenantInvitation.id == invitation_id,
            tenant_invitation_service.TenantInvitation.tenant_id == customer.id,
            tenant_invitation_service.TenantInvitation.invited_by_user_id == ctx.user_id,
        )
    )).scalar_one_or_none()
    if owned_invitation is None:
        raise HTTPException(status_code=404, detail="Reseller-created invitation not found")
    invitation = await tenant_invitation_service.revoke_invitation(
        db,
        tenant_id=customer.id,
        invitation_id=invitation_id,
        actor_id=ctx.user_id,
    )
    await audit_service.record(
        db,
        action="reseller.customer_user.invitation_revoked",
        actor_type="user",
        actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        resource_type="tenant_invitation",
        resource_id=str(invitation.id),
        metadata={
            "actor_tenant_id": str(ctx.tenant_id),
            "target_tenant_id": str(customer.id),
            "target_user_id": str(invitation.user_id),
        },
    )
    return APIResponse(success=True, data=TenantInvitationRevokedResponse(
        id=invitation.id,
        revoked_at=invitation.revoked_at,
    ))


@router.post("/{user_id}/status", response_model=APIResponse[CustomerUserSummary])
async def update_customer_user_status(
    customer_id: UUID,
    user_id: UUID,
    payload: CustomerUserStatusRequest,
    ctx: ResellerCustomerManageContext,
    db: DbSession,
):
    customer = await _load_direct_customer(customer_id, ctx, db, lock=True)
    user = (await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id, User.tenant_id == customer.id)
        .with_for_update()
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Customer user not found")
    if user.is_active and not payload.is_active and any(role.tenant_id == customer.id and role.name.lower() in {'admin', 'owner', 'tenant_admin'} for role in user.roles):
        active_admin_count = (await db.execute(select(func.count(func.distinct(User.id))).select_from(User).join(user_roles, user_roles.c.user_id == User.id).join(Role, Role.id == user_roles.c.role_id).where(User.tenant_id == customer.id, User.is_active.is_(True), Role.tenant_id == customer.id, func.lower(Role.name).in_({'admin', 'owner', 'tenant_admin'})))).scalar_one()
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail='Cannot deactivate the last active Customer administrator')
    if not user.is_active and payload.is_active:
        accepted_invitation = (await db.execute(select(TenantInvitation.id).where(TenantInvitation.user_id == user.id, TenantInvitation.tenant_id == customer.id, TenantInvitation.accepted_at.is_not(None), TenantInvitation.revoked_at.is_(None)).limit(1))).scalar_one_or_none()
        if accepted_invitation is None:
            raise HTTPException(status_code=409, detail='Customer users must accept an invitation before activation')
        if not await tenant_access_service.tenant_has_access(db, tenant=customer):
            raise HTTPException(status_code=402, detail='Customer tenant requires paid or active Demo entitlement')
    if user.is_active != payload.is_active:
        user.is_active = payload.is_active
        user.auth_token_version += 1
        await audit_service.record(
            db,
            action="customer.user_status_updated",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=customer.id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={"is_active": payload.is_active, "actor_tenant_id": str(ctx.tenant_id)},
        )
        await audit_service.record(
            db,
            action="reseller.customer_user.status_updated",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={"target_tenant_id": str(customer.id), "is_active": payload.is_active},
        )
        await db.flush()
    return APIResponse(success=True, data=CustomerUserSummary(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[role.name for role in user.roles if role.tenant_id == customer.id],
    ))

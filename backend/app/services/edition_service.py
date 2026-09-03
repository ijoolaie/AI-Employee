"""Runtime policy and provisioning for the vendor -> reseller -> customer hierarchy."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import request_id_var
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.role import Permission, Role, role_permissions, user_roles
from app.models.support_escalation import SupportEscalation
from app.models.tenant import Tenant
from app.models.tenant_entitlement import TenantEntitlement
from app.models.user import User

EDITION_VENDOR = "vendor"
EDITION_RESELLER = "reseller"
EDITION_CUSTOMER = "customer"

RESELLER_PERMISSIONS = {
    "employee.read", "employee.write", "run.read", "run.execute", "file.read", "file.write",
    "audit.read", "workflow.read", "workflow.write", "workflow.execute", "workflow.cancel",
    "workflow.approval.read", "workflow.approval.decide", "workflow.event.read", "workflow.event.write",
    "memory.read", "memory.write", "memory.delete", "feedback.create", "feedback.read",
    "reseller.customer.create", "reseller.customer.read", "reseller.customer.manage",
    "reseller.entitlement.delegate", "support.escalation.create", "team.install", "team.execute",
}
CUSTOMER_PERMISSIONS = {
    "employee.read", "employee.write", "run.read", "run.execute", "file.read", "file.write",
    "audit.read", "workflow.read", "workflow.write", "workflow.execute", "workflow.cancel",
    "workflow.approval.read", "workflow.approval.decide", "workflow.event.read", "workflow.event.write",
    "memory.read", "memory.write", "memory.delete", "feedback.create", "feedback.read",
    "support.escalation.create", "team.install", "team.execute",
}


def require_edition(ctx, kind: str) -> None:
    if ctx.tenant.tenant_kind != kind:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{kind.title()} edition access required")
    if not ctx.user.is_superuser and not any(role.tenant_id == ctx.tenant_id and role.name.lower() in {"admin", "owner", "tenant_admin"} for role in ctx.user.roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Edition administrator access required")


def assert_direct_child(parent: Tenant, child: Tenant, expected_kind: str) -> None:
    if child.parent_tenant_id != parent.id or child.tenant_kind != expected_kind:
        raise HTTPException(status_code=403, detail="Tenant is outside the permitted edition boundary")


def assert_can_access(actor: Tenant, target: Tenant) -> None:
    """Downstream users may never traverse upward or sideways."""
    if actor.id == target.id:
        return
    if actor.tenant_kind == EDITION_RESELLER and target.parent_tenant_id == actor.id and target.tenant_kind == EDITION_CUSTOMER:
        return
    if actor.tenant_kind == EDITION_VENDOR and target.parent_tenant_id == actor.id and target.tenant_kind == EDITION_RESELLER:
        return
    raise HTTPException(status_code=403, detail="Cross-edition tenant access denied")


async def _ensure_role(db: AsyncSession, tenant: Tenant, name: str, permissions: set[str]) -> Role:
    role = (await db.execute(select(Role).where(Role.tenant_id == tenant.id, Role.name == name))).scalar_one_or_none()
    if role is None:
        role = Role(tenant_id=tenant.id, name=name, description=f"{tenant.tenant_kind} edition administrator")
        db.add(role)
        await db.flush()
    for code in permissions:
        permission = (await db.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
        if permission is None:
            permission = Permission(code=code, description=f"Edition permission: {code}")
            db.add(permission)
            await db.flush()
        await db.execute(insert(role_permissions).values(role_id=role.id, permission_id=permission.id).on_conflict_do_nothing())
    return role


async def provision_child_tenant(db: AsyncSession, *, parent: Tenant, name: str, slug: str, admin_email: str, admin_password: str, full_name: str | None, kind: str, vendor_release_tag: str | None, delivery_revision: str | None) -> tuple[Tenant, User]:
    expected_parent_kind = EDITION_VENDOR if kind == EDITION_RESELLER else EDITION_RESELLER
    if parent.tenant_kind != expected_parent_kind:
        raise HTTPException(status_code=403, detail="Invalid parent edition")
    existing = (await db.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")
    tenant = Tenant(name=name, slug=slug, status="active", tenant_kind=kind, parent_tenant_id=parent.id, vendor_release_tag=vendor_release_tag or parent.vendor_release_tag, delivery_revision=delivery_revision, settings={"edition": kind, "control_plane_parent": str(parent.id)})
    db.add(tenant)
    await db.flush()
    user = User(tenant_id=tenant.id, email=admin_email.lower(), password_hash=hash_password(admin_password), full_name=full_name, is_active=True, is_superuser=True)
    db.add(user)
    await db.flush()
    role_permissions_for_kind = RESELLER_PERMISSIONS if kind == EDITION_RESELLER else CUSTOMER_PERMISSIONS
    role = await _ensure_role(db, tenant, "Admin", role_permissions_for_kind)
    await db.execute(insert(user_roles).values(user_id=user.id, role_id=role.id).on_conflict_do_nothing())
    await db.flush()
    return tenant, user

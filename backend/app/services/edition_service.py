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
    "reseller.entitlement.delegate", "support.escalation.create",
}
CUSTOMER_PERMISSIONS = {
    "employee.read", "employee.write", "run.read", "run.execute", "file.read", "file.write",
    "audit.read", "workflow.read", "workflow.write", "workflow.execute", "workflow.cancel",
    "workflow.approval.read", "workflow.approval.decide", "workflow.event.read", "workflow.event.write",
    "memory.read", "memory.write", "memory.delete", "feedback.create", "feedback.read",
    "support.escalation.create",
}


def require_edition(ctx, kind: str) -> None:
    if ctx.tenant.tenant_kind != kind:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{kind.title()} edition access required")
    if not ctx.user.is_superuser and not any(
        role.tenant_id == ctx.tenant_id and role.name.lower() in {"admin", "owner", "tenant_admin"}
        for role in ctx.user.roles
    ):
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


async def provision_child_tenant(
    db: AsyncSession,
    *,
    parent: Tenant,
    name: str,
    slug: str,
    admin_email: str,
    admin_password: str,
    full_name: str | None,
    kind: str,
    vendor_release_tag: str | None,
    delivery_revision: str | None,
) -> tuple[Tenant, User]:
    expected_parent_kind = EDITION_VENDOR if kind == EDITION_RESELLER else EDITION_RESELLER
    if parent.tenant_kind != expected_parent_kind:
        raise HTTPException(status_code=403, detail="Invalid parent edition")

    existing = (await db.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    tenant = Tenant(
        name=name,
        slug=slug,
        status="active",
        tenant_kind=kind,
        parent_tenant_id=parent.id,
        vendor_release_tag=vendor_release_tag or parent.vendor_release_tag,
        delivery_revision=delivery_revision,
        settings={"edition": kind, "control_plane_parent": str(parent.id)},
    )
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=admin_email.lower(),
        password_hash=hash_password(admin_password),
        full_name=full_name,
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    await db.flush()

    permissions = RESELLER_PERMISSIONS if kind == EDITION_RESELLER else CUSTOMER_PERMISSIONS
    role = await _ensure_role(db, tenant, "Admin", permissions)
    await db.execute(insert(user_roles).values(user_id=user.id, role_id=role.id).on_conflict_do_nothing())

    await record_audit(
        db,
        tenant_id=parent.id,
        actor_id=None,
        action=f"edition.{kind}.provisioned",
        resource_type="tenant",
        resource_id=str(tenant.id),
        metadata={"child_tenant_id": str(tenant.id), "child_kind": kind, "delivery_revision": delivery_revision},
    )
    await db.commit()
    await db.refresh(tenant)
    await db.refresh(user)
    return tenant, user


async def _authorized_parent_entitlement(
    db: AsyncSession, *, parent: Tenant, feature_code: str, requested_quota: int | None
) -> int | None:
    """Return the quota a reseller is allowed to delegate from its own parent."""
    if parent.tenant_kind == EDITION_VENDOR:
        return requested_quota
    row = (await db.execute(select(TenantEntitlement).where(
        TenantEntitlement.tenant_id == parent.id,
        TenantEntitlement.feature_code == feature_code,
        TenantEntitlement.is_enabled.is_(True),
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=403, detail="Feature entitlement is not authorized by the parent edition")
    if row.quota_limit is not None and requested_quota is not None and requested_quota > row.quota_limit:
        raise HTTPException(status_code=403, detail="Delegated quota exceeds the parent-authorized limit")
    return row.quota_limit if requested_quota is None else requested_quota


async def delegate_entitlement(
    db: AsyncSession,
    *,
    parent: Tenant,
    child: Tenant,
    feature_code: str,
    quota_limit: int | None,
) -> TenantEntitlement:
    expected_kind = EDITION_RESELLER if parent.tenant_kind == EDITION_VENDOR else EDITION_CUSTOMER
    assert_direct_child(parent, child, expected_kind)
    effective_quota = await _authorized_parent_entitlement(
        db, parent=parent, feature_code=feature_code, requested_quota=quota_limit
    )
    row = (await db.execute(select(TenantEntitlement).where(
        TenantEntitlement.tenant_id == child.id,
        TenantEntitlement.feature_code == feature_code,
    ))).scalar_one_or_none()
    if row is None:
        row = TenantEntitlement(
            tenant_id=child.id,
            delegated_from_tenant_id=parent.id,
            feature_code=feature_code,
            quota_limit=effective_quota,
            quota_used=0,
            is_enabled=True,
        )
        db.add(row)
    else:
        row.quota_limit = effective_quota
        row.is_enabled = True
        row.delegated_from_tenant_id = parent.id
    await db.commit()
    await db.refresh(row)
    await record_audit(db, tenant_id=parent.id, actor_id=None, action="entitlement.delegated", resource_type="tenant_entitlement", resource_id=str(row.id), metadata={"child_tenant_id": str(child.id), "feature_code": feature_code, "quota_limit": effective_quota})
    return row


async def create_support_escalation(
    db: AsyncSession,
    *,
    from_tenant: Tenant,
    opened_by: UUID,
    subject: str,
    description: str,
) -> SupportEscalation:
    if from_tenant.parent_tenant_id is None:
        raise HTTPException(status_code=400, detail="Root vendor tenants cannot escalate upward")
    target = (await db.execute(select(Tenant).where(Tenant.id == from_tenant.parent_tenant_id))).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=409, detail="Parent support tenant unavailable")
    row = SupportEscalation(from_tenant_id=from_tenant.id, to_tenant_id=target.id, opened_by=opened_by, subject=subject, description=description, extra_data={})
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await record_audit(db, tenant_id=from_tenant.id, actor_id=opened_by, action="support.escalation.created", resource_type="support_escalation", resource_id=str(row.id), metadata={"to_tenant_id": str(target.id)})
    return row


async def record_audit(db: AsyncSession, *, tenant_id, actor_id, action: str, resource_type: str, resource_id: str, metadata: dict) -> None:
    db.add(AuditLog(
        tenant_id=tenant_id,
        actor_type="user" if actor_id else "system",
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id_var.get(),
        status="success",
        metadata=metadata,
    ))
    await db.commit()

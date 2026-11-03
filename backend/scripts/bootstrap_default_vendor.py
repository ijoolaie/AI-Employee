"""Idempotently bootstrap the configured root Vendor and its first least-privilege Admin.

Operator-only invocation:
  DEFAULT_VENDOR_TENANT_SLUG=... DEFAULT_VENDOR_BOOTSTRAP_TENANT_NAME=... \
  DEFAULT_VENDOR_BOOTSTRAP_ADMIN_EMAIL=... DEFAULT_VENDOR_BOOTSTRAP_ADMIN_PASSWORD=... \
  python scripts/bootstrap_default_vendor.py

The script never promotes the Admin to superuser/platform-admin and never creates
a Vendor during public signup.
"""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.role import Permission, Role, role_permissions, user_roles
from app.models.tenant import Tenant
from app.models.user import User
from app.services import audit_service


VENDOR_ADMIN_PERMISSIONS = (
    "vendor.tenant.read",
    "vendor.reseller.read",
    "vendor.reseller.create",
    "vendor.reseller.manage",
    "vendor.customer.read",
    "vendor.customer.create",
    "vendor.customer.manage",
)


async def bootstrap() -> None:
    settings = get_settings()
    slug = (settings.default_vendor_tenant_slug or "").strip()
    if not slug:
        raise SystemExit("DEFAULT_VENDOR_TENANT_SLUG must be configured before bootstrap")

    name = os.environ.get("DEFAULT_VENDOR_BOOTSTRAP_TENANT_NAME", "").strip()
    email = os.environ.get("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_PASSWORD", "")
    if not email:
        raise SystemExit("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_EMAIL is required")
    if "@" not in email:
        raise SystemExit("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_EMAIL must be a valid email")

    async with AsyncSessionLocal() as db:
        await db.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"default-vendor-bootstrap:{slug}"))))
        vendor = (await db.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one_or_none()
        created_vendor = False
        if vendor is None:
            if len(name) < 2:
                raise SystemExit("DEFAULT_VENDOR_BOOTSTRAP_TENANT_NAME is required when creating the Vendor")
            vendor = Tenant(
                name=name,
                slug=slug,
                status="active",
                tenant_kind="vendor",
                parent_tenant_id=None,
                settings={"edition": "vendor", "provisioning": "operator-bootstrap"},
            )
            db.add(vendor)
            await db.flush()
            created_vendor = True
        elif vendor.tenant_kind != "vendor" or vendor.parent_tenant_id is not None:
            raise SystemExit("Configured slug exists but is not a root Vendor; refusing to modify it")
        elif vendor.status != "active":
            raise SystemExit("Configured root Vendor is not active; refusing to reactivate it")

        user = (await db.execute(
            select(User).where(User.tenant_id == vendor.id, User.email == email)
        )).scalar_one_or_none()
        created_user = False
        if user is None:
            if len(password) < 12:
                raise SystemExit("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_PASSWORD (minimum 12 characters) is required for a new Admin")
            user = User(
                tenant_id=vendor.id,
                email=email,
                password_hash=hash_password(password),
                full_name=os.environ.get("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_FULL_NAME") or "Vendor Administrator",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
            )
            db.add(user)
            await db.flush()
            created_user = True
        elif not user.is_active or user.is_superuser or user.is_platform_admin:
            raise SystemExit("Existing bootstrap user is inactive or privileged; refusing implicit changes")

        role = (await db.execute(
            select(Role).where(Role.tenant_id == vendor.id, Role.name == "Admin")
        )).scalar_one_or_none()
        if role is None:
            role = Role(tenant_id=vendor.id, name="Admin", description="Root Vendor control-plane administrator")
            db.add(role)
            await db.flush()

        grants_added: list[str] = []
        for code in VENDOR_ADMIN_PERMISSIONS:
            permission = (await db.execute(
                select(Permission).where(Permission.code == code)
            )).scalar_one_or_none()
            if permission is None:
                await db.execute(
                    insert(Permission)
                    .values(code=code, description=f"Vendor control-plane permission: {code}")
                    .on_conflict_do_nothing(index_elements=[Permission.code])
                )
                permission = (await db.execute(
                    select(Permission).where(Permission.code == code)
                )).scalar_one()
            grant_result = await db.execute(
                insert(role_permissions)
                .values(role_id=role.id, permission_id=permission.id)
                .on_conflict_do_nothing()
            )
            if grant_result.rowcount:
                grants_added.append(code)

        assignment_result = await db.execute(
            insert(user_roles)
            .values(user_id=user.id, role_id=role.id)
            .on_conflict_do_nothing()
        )
        if assignment_result.rowcount:
            await audit_service.record(
                db,
                action="vendor.bootstrap.admin_role_assigned",
                actor_type="system",
                tenant_id=vendor.id,
                resource_type="role",
                resource_id=role.id,
                metadata={"admin_user_id": str(user.id), "role": role.name},
            )
        if grants_added:
            await audit_service.record(
                db,
                action="vendor.bootstrap.permissions_granted",
                actor_type="system",
                tenant_id=vendor.id,
                resource_type="role",
                resource_id=role.id,
                metadata={"permission_codes": sorted(grants_added)},
            )

        if created_vendor:
            await audit_service.record(
                db,
                action="vendor.bootstrap.created",
                actor_type="system",
                tenant_id=vendor.id,
                resource_type="tenant",
                resource_id=vendor.id,
                metadata={"tenant_slug": vendor.slug, "admin_user_id": str(user.id)},
            )
        if created_user:
            await audit_service.record(
                db,
                action="vendor.bootstrap.admin_created",
                actor_type="system",
                tenant_id=vendor.id,
                resource_type="user",
                resource_id=user.id,
                metadata={"admin_email": user.email, "role": role.name},
            )

        await db.commit()
        print(f"Default Vendor ready: {vendor.slug}; Admin: {user.email}; created_vendor={created_vendor}; created_user={created_user}")


if __name__ == "__main__":
    asyncio.run(bootstrap())
"""CI-only Platform Admin fixture for isolated real-stack tests."""
from __future__ import annotations
import asyncio
import os
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User

_CREDENTIALS: tuple[str, str] | None = None

async def ensure_credentials():
    global _CREDENTIALS
    if _CREDENTIALS is not None:
        return _CREDENTIALS
    vendor_slug = os.environ.get("DEFAULT_VENDOR_TENANT_SLUG", "ci-default-vendor")
    email = os.environ.get("CI_PLATFORM_ADMIN_EMAIL", "ci-platform-admin@example.com").strip().lower()
    password = os.environ.get("CI_PLATFORM_ADMIN_PASSWORD", "ci-only-platform-admin-password-2026")
    async with AsyncSessionLocal() as db:
        vendor = (await db.execute(select(Tenant).where(
            Tenant.slug == vendor_slug, Tenant.tenant_kind == "vendor",
            Tenant.parent_tenant_id.is_(None), Tenant.status == "active",
        ))).scalar_one_or_none()
        assert vendor is not None, f"active root Vendor fixture not found: {vendor_slug}"
        user = (await db.execute(select(User).where(
            User.tenant_id == vendor.id, User.email == email,
        ).with_for_update())).scalar_one_or_none()
        if user is None:
            user = User(
                tenant_id=vendor.id, email=email, password_hash=hash_password(password),
                full_name="CI Platform Admin", is_active=True,
                is_superuser=False, is_platform_admin=True,
            )
            db.add(user)
            await db.commit()
        else:
            assert user.is_active and user.is_platform_admin and not user.is_superuser
    _CREDENTIALS = (email, password)
    return _CREDENTIALS

def credentials():
    if _CREDENTIALS is not None:
        return _CREDENTIALS
    return asyncio.run(ensure_credentials())

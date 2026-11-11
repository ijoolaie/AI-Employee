"""PostgreSQL HTTP acceptance for preserving a tenant's last active administrator."""

import asyncio
import os
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _database_url() -> str:
    url = os.environ.get("SUPPORT_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("Test database URL is required; refusing to run.")
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.username != "support_test_user"
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port != 15433
        or parsed.database != "support_test"
        or not parsed.password
    ):
        raise RuntimeError("URL must target the dedicated local support_test database; refusing to run.")
    return url


@pytest.mark.asyncio
async def test_concurrent_deactivation_cannot_remove_all_tenant_admins():
    db_url = _database_url()
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models.role import Permission, Role
    from app.models.tenant import Tenant
    from app.models.user import User

    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    run_id = uuid.uuid4().hex
    tenant = Tenant(
        name=f"Last admin race {run_id}",
        slug=f"last-admin-race-{run_id}",
        status="active",
        tenant_kind="customer",
        settings={},
    )
    try:
        async with sessions() as session:
            session.add(tenant)
            await session.flush()
            permission = (await session.execute(
                select(Permission).where(Permission.code == "tenant.users.manage")
            )).scalar_one_or_none()
            if permission is None:
                permission = Permission(code="tenant.users.manage", description="Manage tenant users")
                session.add(permission)
                await session.flush()
            admin_role = Role(tenant_id=tenant.id, name="Admin", description="Last-admin race test")
            admin_role.permissions = [permission]
            session.add(admin_role)
            users = [
                User(
                    tenant_id=tenant.id,
                    email=f"last-admin-{index}-{run_id}@example.com",
                    password_hash="not-used",
                    full_name=f"Admin {index}",
                    is_active=True,
                    is_superuser=False,
                    is_platform_admin=False,
                    roles=[admin_role],
                )
                for index in range(3)
            ]
            session.add_all(users)
            await session.commit()

        async def override_get_db() -> AsyncIterator[AsyncSession]:
            async with sessions() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        missing = object()
        previous = app.dependency_overrides.get(get_db, missing)
        app.dependency_overrides[get_db] = override_get_db
        try:
            actor = users[2]
            token = create_access_token(
                subject=actor.id,
                tenant_id=tenant.id,
                extra_claims={"auth_token_version": actor.auth_token_version},
            )
            headers = {"Authorization": f"Bearer {token}"}
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                async def deactivate(target: User):
                    return await client.post(
                        f"/api/v1/tenant-admin/users/{target.id}/status",
                        headers=headers,
                        json={"is_active": False},
                    )

                responses = await asyncio.gather(deactivate(users[0]), deactivate(users[1]))
                assert sorted(response.status_code for response in responses) == [200, 200], [
                    (response.status_code, response.text) for response in responses
                ]

            async with sessions() as session:
                remaining = (await session.execute(
                    select(User).where(User.tenant_id == tenant.id, User.is_active.is_(True))
                )).scalars().all()
                active_admins = [
                    user for user in remaining
                    if any(role.tenant_id == tenant.id and role.name.lower() in {"admin", "owner", "tenant_admin"}
                           for role in user.roles)
                ]
                assert len(active_admins) == 1
                assert active_admins[0].id == actor.id
        finally:
            if previous is missing:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
    finally:
        await engine.dispose()



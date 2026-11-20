"""Live HTTP/PostgreSQL acceptance for legacy Employee Marketplace snapshots."""

import os
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _database_url() -> str:
    raw = os.environ.get("SUPPORT_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not raw:
        raise RuntimeError("Dedicated local support_test database URL is required; refusing to run.")
    parsed = make_url(raw)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.username not in {"support_test_user", "aiep"}
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433}
        or parsed.database != "support_test"
        or not parsed.password
    ):
        raise RuntimeError("URL must target the dedicated local support_test database; refusing to run.")
    return raw


@pytest.mark.asyncio
async def test_install_rejects_legacy_secret_and_execution_authority_snapshots():
    database_url = _database_url()
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models.agent_definition import AgentDefinition
    from app.models.agent_template import AgentTemplate, AgentTemplateStatus
    from app.models.employee_marketplace import (
        EmployeeMarketplaceInstallation,
        EmployeeMarketplacePackage,
        EmployeeMarketplacePackageStatus,
    )
    from app.models.role import Permission, Role
    from app.models.tenant import Tenant
    from app.models.user import User

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    run_id = uuid.uuid4().hex
    seller = Tenant(name=f"Marketplace seller {run_id}", slug=f"market-seller-{run_id}", status="active", tenant_kind="vendor", settings={})
    buyer = Tenant(name=f"Marketplace buyer {run_id}", slug=f"market-buyer-{run_id}", status="active", tenant_kind="customer", settings={})
    actor_id = uuid.uuid4()
    package_ids = [uuid.uuid4(), uuid.uuid4()]
    missing = object()
    previous = None
    try:
        async with sessions() as session:
            session.add_all([seller, buyer])
            await session.flush()
            permission = (await session.execute(select(Permission).where(Permission.code == "employee_marketplace.install"))).scalar_one_or_none()
            if permission is None:
                permission = Permission(code="employee_marketplace.install", description="Install public employee marketplace packages")
                session.add(permission)
                await session.flush()
            definition = AgentDefinition(
                tenant_id=seller.id,
                slug=f"legacy-market-source-{run_id}",
                name="Legacy marketplace source",
                version=1,
                capabilities=[],
                allowed_tools=[],
                model_policy={},
                input_schema={},
                output_schema={},
                policy_requirements={},
                enabled=True,
            )
            session.add(definition)
            await session.flush()
            template = AgentTemplate(
                tenant_id=seller.id,
                agent_definition_id=definition.id,
                slug=f"legacy-market-template-{run_id}",
                name="Legacy marketplace template",
                version=1,
                status=AgentTemplateStatus.PUBLISHED,
                risk_tier=1,
                capability_contract={},
                permission_policy={},
                approval_policy={},
                evaluation_policy={},
                install_policy={},
                is_system_template=False,
            )
            session.add(template)
            role = Role(tenant_id=buyer.id, name=f"marketplace-installer-{run_id}", description="Acceptance installer")
            session.add(role)
            role.permissions = [permission]
            actor = User(
                id=actor_id,
                tenant_id=buyer.id,
                email=f"marketplace-installer-{run_id}@example.test",
                password_hash="unused-test-hash",
                full_name="Marketplace Installer",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                auth_token_version=0,
            )
            session.add(actor)
            actor.roles = [role]
            await session.flush()

            base_manifest = {
                "template_snapshot": {
                    "name": "Legacy marketplace template",
                    "version": 1,
                    "risk_tier": 1,
                    "capability_contract": {},
                    "permission_policy": {},
                    "approval_policy": {},
                    "evaluation_policy": {},
                },
                "definition_snapshot": {
                    "name": "Legacy marketplace source",
                    "version": 1,
                    "capabilities": [],
                    "allowed_tools": [],
                    "input_schema": {},
                    "output_schema": {},
                    "policy_requirements": {},
                },
            }
            secret_manifest = {
                **base_manifest,
                "definition_snapshot": {
                    **base_manifest["definition_snapshot"],
                    "model_policy": {"provider": {"access-token": "legacy-secret"}},
                },
            }
            authority_manifest = {
                **base_manifest,
                "template_snapshot": {
                    **base_manifest["template_snapshot"],
                    "install_policy": {"workflow": [{"bypass_approval": True}]},
                },
            }
            for package_id, slug, manifest in (
                (package_ids[0], f"legacy-secret-{run_id}", secret_manifest),
                (package_ids[1], f"legacy-authority-{run_id}", authority_manifest),
            ):
                session.add(
                    EmployeeMarketplacePackage(
                        id=package_id,
                        owner_tenant_id=seller.id,
                        source_agent_template_id=template.id,
                        slug=slug,
                        name=slug,
                        version=1,
                        status=EmployeeMarketplacePackageStatus.PUBLISHED,
                        visibility="public",
                        risk_tier=1,
                        employee_manifest=manifest,
                        permission_manifest={"requested_permissions": [], "approval_policy": {}},
                        skill_package_ids=[],
                        workflow_refs=[],
                        visual_pack={},
                    )
                )
            await session.commit()

        async def override_get_db() -> AsyncIterator[AsyncSession]:
            async with sessions() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        from app.core.database import get_db as dependency_key
        from app.core.security import create_access_token

        previous = app.dependency_overrides.get(dependency_key, missing)
        app.dependency_overrides[dependency_key] = override_get_db
        token = create_access_token(subject=actor_id, tenant_id=buyer.id, extra_claims={"auth_token_version": 0})
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                for package_id in package_ids:
                    response = await client.post(
                        f"/api/v1/employee-marketplace/packages/{package_id}/install",
                        headers=headers,
                        json={"sponsor_user_id": str(actor_id)},
                    )
                    assert response.status_code == 422, response.text
        finally:
            if previous is missing:
                app.dependency_overrides.pop(dependency_key, None)
            else:
                app.dependency_overrides[dependency_key] = previous

        async with sessions() as session:
            installs = await session.scalar(
                select(func.count()).select_from(EmployeeMarketplaceInstallation).where(
                    EmployeeMarketplaceInstallation.buyer_tenant_id == buyer.id,
                    EmployeeMarketplaceInstallation.package_id.in_(package_ids),
                )
            )
            imported = await session.scalar(
                select(func.count()).select_from(AgentDefinition).where(
                    AgentDefinition.tenant_id == buyer.id,
                    AgentDefinition.slug.like("marketplace-%"),
                )
            )
            assert installs == 0
            assert imported == 0
    finally:
        if previous is not missing and previous is not None:
            app.dependency_overrides[get_db] = previous
        await engine.dispose()

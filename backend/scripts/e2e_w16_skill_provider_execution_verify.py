"""Real-stack W16 installed SkillPackage provider execution verification."""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy import select

from app.ai.tool_registry import registry
from app.core.database import AsyncSessionLocal
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.product import Product
from app.models.skill_package import EmployeeSkillInstallationStatus, SkillPackageStatus
from app.models.tenant import Tenant
from app.services import edition_lifecycle_service, skill_marketplace_service
from app.services import license_service

PROVIDER_STATE = Path("/tmp/w16-skill-provider-last.json")
PROVIDER_HEALTH = "http://127.0.0.1:18181/health"
TOOL = "workforce_execute_installed_skill"


async def fixture() -> tuple[list[str], uuid.UUID, uuid.UUID, uuid.UUID]:
    suffix = str(time.time_ns())[-12:]
    slugs = [f"w16-skill-exec-a-{suffix}", f"w16-skill-exec-b-{suffix}"]

    async with AsyncSessionLocal() as db:
        async with db.begin():
            tenant_a = Tenant(name="W16 Skill Provider A", slug=slugs[0])
            tenant_b = Tenant(name="W16 Skill Provider B", slug=slugs[1])
            db.add_all([tenant_a, tenant_b])
            await db.flush()

            employee_a = Employee(
                tenant_id=tenant_a.id,
                slug=f"w16-skill-exec-employee-{suffix}",
                name="W16 Skill Execution Employee",
                kind="custom",
                is_active=True,
            )
            db.add(employee_a)
            await db.flush()

            package = await skill_marketplace_service.create_package(
                db,
                tenant_id=tenant_a.id,
                slug=f"w16-provider-skill-{suffix}",
                name="W16 Provider Skill",
                version=1,
                manifest={"contract_version": "w16-provider-v1"},
                compatibility={"runtime": "ci"},
                presentation_metadata={"label": "provider execution"},
            )
            await skill_marketplace_service.publish_package(
                db,
                tenant_id=tenant_a.id,
                package_id=package.id,
                actor_id=uuid.uuid4(),
            )
            installation = await skill_marketplace_service.install(
                db,
                tenant_id=tenant_a.id,
                employee_id=employee_a.id,
                skill_package_id=package.id,
            )
            assert installation.status == EmployeeSkillInstallationStatus.ACTIVE

            await license_service.issue_license(
                db,
                issuer=tenant_b,
                tenant=tenant_a,
                feature_codes=["employee.run"],
                metadata={"certification_fixture": True, "purpose": "w16-skill-provider-execution"},
            )

            return slugs, tenant_a.id, tenant_b.id, employee_a.id


async def commercial_fixture(tenant_id: uuid.UUID, employee_id: uuid.UUID) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        product = Product(
            tenant_id=tenant_id,
            sku=f"w16-skill-provider-commercial-{uuid.uuid4().hex[:8]}",
            name="W16 Commercial Provider Skill",
            description="Commercial provider execution fixture",
            category="employee_skill",
            price=10,
            currency="EUR",
            inventory=10,
            attributes={
                "skill_package_slug": f"commercial-provider-skill-{uuid.uuid4().hex[:8]}",
                "skill_package_version": 1,
            },
            is_active=True,
        )
        db.add(product)
        await db.flush()
        package = await skill_marketplace_service.create_package(
            db,
            tenant_id=tenant_id,
            slug=product.attributes["skill_package_slug"],
            name="Commercial Provider Skill",
            version=1,
            product_id=product.id,
            manifest={},
            compatibility={},
            presentation_metadata={},
        )
        await skill_marketplace_service.publish_package(
            db,
            tenant_id=tenant_id,
            package_id=package.id,
            actor_id=uuid.uuid4(),
        )
        await skill_marketplace_service.install(
            db,
            tenant_id=tenant_id,
            employee_id=employee_id,
            skill_package_id=package.id,
        )
        await db.commit()
        return package.id


async def cleanup(slugs: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        tenants = list((await db.execute(select(Tenant).where(Tenant.slug.in_(slugs)))).scalars().all())
        for tenant in tenants:
            if tenant.status != edition_lifecycle_service.STATUS_DEPROVISIONED:
                await edition_lifecycle_service.transition_tenant_status(
                    db,
                    tenant=tenant,
                    target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
                    actor_id=None,
                    audit_tenant_id=tenant.id,
                    audit_metadata={"certification_fixture": True, "cleanup_mode": "deprovision"},
                )
        await db.commit()


async def verify() -> None:
    slugs, tenant_a_id, tenant_b_id, employee_a_id = await fixture()
    try:
        while True:
            try:
                with urlopen(PROVIDER_HEALTH, timeout=2) as response:
                    if response.status == 200:
                        break
            except Exception:
                await asyncio.sleep(0.2)

        request_id = f"w16-skill-provider-{uuid.uuid4()}"
        with pytest_approval_context():
            async with AsyncSessionLocal() as db:
                try:
                    await registry.execute(
                        TOOL,
                        {"skill_package_id": "00000000-0000-0000-0000-000000000001", "input": {}},
                        permissions={"run.execute"},
                        allowed_tools={TOOL},
                        db=db,
                        tenant_id=tenant_a_id,
                        employee_id=employee_a_id,
                        approval_granted=False,
                        tool_call_id=request_id,
                    )
                except ValidationAppError as exc:
                    assert "Human approval required" in str(exc)
                    print("SKILL PROVIDER EXECUTION APPROVAL GATE PASS")
                else:
                    raise AssertionError("unapproved skill provider execution was accepted")

        async with AsyncSessionLocal() as db:
            package = (
                await db.execute(
                    select(
                        __import__("app.models.skill_package", fromlist=["SkillPackage"]).SkillPackage
                    ).where(
                        __import__("app.models.skill_package", fromlist=["SkillPackage"]).SkillPackage.tenant_id == tenant_a_id,
                        __import__("app.models.skill_package", fromlist=["SkillPackage"]).SkillPackage.status == SkillPackageStatus.PUBLISHED,
                        __import__("app.models.skill_package", fromlist=["SkillPackage"]).SkillPackage.product_id.is_(None),
                    )
                )
            ).scalar_one()

            result = await registry.execute(
                TOOL,
                {"skill_package_id": str(package.id), "input": {"message": "hello", "count": 3}},
                permissions={"run.execute"},
                allowed_tools={TOOL},
                db=db,
                tenant_id=tenant_a_id,
                employee_id=employee_a_id,
                approval_granted=True,
                tool_call_id=request_id,
            )
            assert result["provider"] == "http"
            assert result["executed"] is True
            assert result["status"] == "executed"
            assert result["result"]["accepted"] is True
            print("SKILL PROVIDER HTTP EXECUTION PASS")

            provider_payload = json.loads(PROVIDER_STATE.read_text(encoding="utf-8"))
            assert provider_payload["tenant_id"] == str(tenant_a_id)
            assert provider_payload["employee_id"] == str(employee_a_id)
            assert provider_payload["skill_package_id"] == str(package.id)
            assert provider_payload["request_id"] == request_id
            assert provider_payload["input"] == {"message": "hello", "count": 3}
            print("SKILL PROVIDER TENANT + REQUEST CORRELATION PASS")

            logs = await db.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == tenant_a_id,
                    AuditLog.action == "employee_skill.provider_execution",
                )
            )
            entries = list(logs.scalars().all())
            assert entries
            meta = entries[-1].metadata_ or {}
            assert meta["provider"] == "http"
            assert meta["external_execution"] is True
            assert meta["executed"] is True
            assert meta["execution_authority_changed"] is False
            print("SKILL PROVIDER AUDIT PROVENANCE PASS")

        async with AsyncSessionLocal() as db:
            try:
                await registry.execute(
                    TOOL,
                    {"skill_package_id": str(package.id), "input": {}},
                    permissions={"run.execute"},
                    allowed_tools={TOOL},
                    db=db,
                    tenant_id=tenant_b_id,
                    employee_id=employee_a_id,
                    approval_granted=True,
                    tool_call_id=str(uuid.uuid4()),
                )
            except NotFoundError:
                print("SKILL PROVIDER CROSS-TENANT REJECT PASS")
            else:
                raise AssertionError("cross-tenant skill execution was accepted")

            commercial_package_id = await commercial_fixture(tenant_a_id, employee_a_id)

        async with AsyncSessionLocal() as db:
            try:
                await registry.execute(
                    TOOL,
                    {"skill_package_id": str(commercial_package_id), "input": {}},
                    permissions={"run.execute"},
                    allowed_tools={TOOL},
                    db=db,
                    tenant_id=tenant_a_id,
                    employee_id=employee_a_id,
                    approval_granted=True,
                    tool_call_id=str(uuid.uuid4()),
                )
            except ConflictError as exc:
                assert "verified skill purchase entitlement" in str(exc)
                print("COMMERCIAL SKILL PROVIDER EXECUTION FAIL-CLOSED PASS")
            else:
                raise AssertionError("commercial skill provider execution bypassed entitlement")

        print("W16 INSTALLED SKILL PROVIDER EXECUTION REAL-STACK PASS")
    finally:
        await cleanup(slugs)


class pytest_approval_context:
    def __enter__(self): return self
    def __exit__(self, *args): return False


if __name__ == "__main__":
    asyncio.run(verify())

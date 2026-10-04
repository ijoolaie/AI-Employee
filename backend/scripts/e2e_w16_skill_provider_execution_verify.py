"""Real-stack W16 installed SkillPackage provider execution verification."""
from __future__ import annotations

import asyncio
import json
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
from app.models.skill_package import (
    EmployeeSkillInstallation,
    EmployeeSkillInstallationStatus,
    SkillPackage,
    SkillPackageStatus,
)
from app.models.tenant import Tenant
from app.services import edition_lifecycle_service, skill_marketplace_service

PROVIDER_STATE = Path("/tmp/w16-skill-provider-last.json")
PROVIDER_HEALTH = "http://127.0.0.1:18181/health"
TOOL = "workforce_execute_installed_skill"


async def prepare() -> tuple[list[str], uuid.UUID, uuid.UUID, uuid.UUID]:
    suffix = str(time.time_ns())[-12:]
    slug_a = f"w16-skill-exec-a-{suffix}"
    slug_b = f"w16-skill-exec-b-{suffix}"
    async with AsyncSessionLocal() as db:
        tenant_a = Tenant(name="W16 Skill Provider A", slug=slug_a)
        tenant_b = Tenant(name="W16 Skill Provider B", slug=slug_b)
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
        await db.commit()
        return [slug_a, slug_b], tenant_a.id, tenant_b.id, employee_a.id


async def prepare_commercial(
    tenant_id: uuid.UUID, employee_id: uuid.UUID
) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        slug = f"w16-commercial-provider-{uuid.uuid4().hex[:10]}"
        product = Product(
            tenant_id=tenant_id,
            sku=f"w16-commercial-provider-{uuid.uuid4().hex[:10]}",
            name="W16 Commercial Provider Skill",
            description="Commercial provider execution fixture",
            category="employee_skill",
            price=10,
            currency="EUR",
            inventory=10,
            attributes={"skill_package_slug": slug, "skill_package_version": 1},
            is_active=True,
        )
        db.add(product)
        await db.flush()
        package = await skill_marketplace_service.create_package(
            db,
            tenant_id=tenant_id,
            slug=slug,
            name="Commercial Provider Skill",
            version=1,
            product_id=product.id,
        )
        await skill_marketplace_service.publish_package(
            db,
            tenant_id=tenant_id,
            package_id=package.id,
            actor_id=uuid.uuid4(),
        )
        # Fixture-only installation. The normal installation path correctly
        # requires the verified purchase entitlement for commercial packages.
        db.add(
            EmployeeSkillInstallation(
                tenant_id=tenant_id,
                employee_id=employee_id,
                skill_package_id=package.id,
                status=EmployeeSkillInstallationStatus.ACTIVE,
            )
        )
        await db.commit()
        return package.id


async def cleanup(slugs: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        tenants = list(
            (
                await db.execute(
                    select(Tenant).where(Tenant.slug.in_(slugs))
                )
            ).scalars().all()
        )
        for tenant in tenants:
            if tenant.status != edition_lifecycle_service.STATUS_DEPROVISIONED:
                await edition_lifecycle_service.transition_tenant_status(
                    db,
                    tenant=tenant,
                    target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
                    actor_id=None,
                    audit_tenant_id=tenant.id,
                    audit_metadata={
                        "certification_fixture": True,
                        "cleanup_mode": "deprovision",
                    },
                )
        await db.commit()


async def verify() -> None:
    slugs, tenant_a_id, tenant_b_id, employee_a_id = await prepare()
    try:
        for _ in range(30):
            try:
                with urlopen(PROVIDER_HEALTH, timeout=2) as response:
                    if response.status == 200:
                        break
            except Exception:
                await asyncio.sleep(0.2)
        else:
            raise AssertionError("skill provider fixture did not become ready")

        request_id = f"w16-skill-provider-{uuid.uuid4()}"

        async with AsyncSessionLocal() as db:
            package = (
                await db.execute(
                    select(SkillPackage).where(
                        SkillPackage.tenant_id == tenant_a_id,
                        SkillPackage.status == SkillPackageStatus.PUBLISHED,
                        SkillPackage.product_id.is_(None),
                    )
                )
            ).scalar_one()

            try:
                await registry.execute(
                    TOOL,
                    {"skill_package_id": str(package.id), "input": {}},
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

            result = await registry.execute(
                TOOL,
                {
                    "skill_package_id": str(package.id),
                    "input": {"message": "hello", "count": 3},
                },
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

            provider_payload = json.loads(
                PROVIDER_STATE.read_text(encoding="utf-8")
            )
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
            entry = list(logs.scalars().all())[-1]
            metadata = entry.metadata_ or {}
            assert metadata["provider"] == "http"
            assert metadata["external_execution"] is True
            assert metadata["executed"] is True
            assert metadata["execution_authority_changed"] is False
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

        commercial_package_id = await prepare_commercial(tenant_a_id, employee_a_id)

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
                raise AssertionError(
                    "commercial skill provider execution bypassed entitlement"
                )

        print("W16 INSTALLED SKILL PROVIDER EXECUTION REAL-STACK PASS")
    finally:
        await cleanup(slugs)


if __name__ == "__main__":
    asyncio.run(verify())

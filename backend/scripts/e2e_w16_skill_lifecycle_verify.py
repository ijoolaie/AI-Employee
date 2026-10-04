"""Real PostgreSQL W16 skill lifecycle verification.

Exercises the governed service against the CI PostgreSQL database after
Alembic upgrade. The transaction is rolled back, so the script leaves no
test fixtures behind.
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.exceptions import NotFoundError
from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.skill_package import (
    EmployeeSkillInstallationStatus,
    SkillPackageStatus,
)
from app.models.tenant import Tenant
from app.services import audit_service
from app.services.skill_marketplace_service import (
    create_package,
    install,
    publish_package,
    revoke,
)


async def verify() -> None:
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    employee_a_id = uuid.uuid4()
    employee_b_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        async with db.begin():
            tenant_a = Tenant(
                id=tenant_a_id,
                name="W16 Runtime Tenant A",
                slug=f"w16-runtime-a-{uuid.uuid4().hex[:12]}",
            )
            tenant_b = Tenant(
                id=tenant_b_id,
                name="W16 Runtime Tenant B",
                slug=f"w16-runtime-b-{uuid.uuid4().hex[:12]}",
            )
            employee_a = Employee(
                id=employee_a_id,
                tenant_id=tenant_a_id,
                slug=f"w16-runtime-employee-a-{uuid.uuid4().hex[:8]}",
                name="W16 Runtime Employee A",
                kind="custom",
            )
            employee_b = Employee(
                id=employee_b_id,
                tenant_id=tenant_b_id,
                slug=f"w16-runtime-employee-b-{uuid.uuid4().hex[:8]}",
                name="W16 Runtime Employee B",
                kind="custom",
            )
            db.add_all([tenant_a, tenant_b])
            await db.flush()
            db.add_all([employee_a, employee_b])
            await db.flush()

            package = await create_package(
                db,
                tenant_id=tenant_a_id,
                slug=f"w16-runtime-skill-{uuid.uuid4().hex[:8]}",
                name="W16 Runtime Skill",
                version=1,
                manifest={"ui": {"label": "runtime verification"}},
                compatibility={"runtime": "ci"},
                presentation_metadata={"display": "verification"},
            )
            assert package.status == SkillPackageStatus.DRAFT

            await publish_package(
                db,
                tenant_id=tenant_a_id,
                package_id=package.id,
                actor_id=None,
            )
            assert package.status == SkillPackageStatus.PUBLISHED
            assert package.published_at is not None

            installation = await install(
                db,
                tenant_id=tenant_a_id,
                employee_id=employee_a_id,
                skill_package_id=package.id,
                actor_id=None,
            )
            assert installation.status == EmployeeSkillInstallationStatus.ACTIVE

            await revoke(
                db,
                tenant_id=tenant_a_id,
                employee_id=employee_a_id,
                skill_package_id=package.id,
                actor_id=None,
            )
            assert installation.status == EmployeeSkillInstallationStatus.REVOKED
            assert installation.revoked_at is not None

            reactivated = await install(
                db,
                tenant_id=tenant_a_id,
                employee_id=employee_a_id,
                skill_package_id=package.id,
                actor_id=None,
            )
            assert reactivated.id == installation.id
            assert reactivated.status == EmployeeSkillInstallationStatus.ACTIVE
            assert reactivated.revoked_at is None

            for label, tenant_id, employee_id in (
                ("cross-tenant employee", tenant_a_id, employee_b_id),
                ("cross-tenant package", tenant_b_id, employee_b_id),
            ):
                try:
                    await install(
                        db,
                        tenant_id=tenant_id,
                        employee_id=employee_id,
                        skill_package_id=package.id,
                        actor_id=None,
                    )
                except NotFoundError:
                    print(f"PASS: {label} rejected")
                else:
                    raise AssertionError(f"{label} was unexpectedly accepted")

            logs = await audit_service.list_logs(db, tenant_id=tenant_a_id, limit=100)
            actions = [entry.action for entry in logs]
            for expected in (
                "skill_package.published",
                "employee_skill.installed",
                "employee_skill.revoked",
            ):
                assert expected in actions, f"missing audit action: {expected}"

            installed_logs = [
                entry for entry in logs if entry.action == "employee_skill.installed"
            ]
            assert len(installed_logs) == 2
            for entry in installed_logs:
                metadata = entry.metadata_ or {}
                assert metadata.get("presentation_only") is True
                assert metadata.get("execution_authority_changed") is False
                assert metadata.get("permissions_changed") is False
                assert metadata.get("allowed_tools_changed") is False

            ledger = await audit_service.verify_ledger(
                db,
                tenant_id=tenant_a_id,
                limit=100,
            )
            assert ledger["valid"] is True, ledger

            persisted = await db.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == tenant_a_id,
                    AuditLog.action.in_(
                        [
                            "skill_package.published",
                            "employee_skill.installed",
                            "employee_skill.revoked",
                        ]
                    ),
                )
            )
            assert len(list(persisted.scalars().all())) == 4

            print("PASS: W16 real-stack publish/install/revoke/reactivate lifecycle")
            print("PASS: W16 cross-tenant install attempts rejected")
            print("PASS: W16 audit provenance recorded for lifecycle mutations")
            print("PASS: W16 tenant audit ledger verifies")
            print("PASS: W16 lifecycle verification transaction will be rolled back")


if __name__ == "__main__":
    asyncio.run(verify())

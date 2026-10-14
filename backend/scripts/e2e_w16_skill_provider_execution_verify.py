"""Real-stack W16 installed SkillPackage provider execution verification."""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy import select

from app.ai.tool_registry import registry
from app.core.database import AsyncSessionLocal
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.audit_log import AuditLog
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.agent_instance import AgentInstance
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.models.tool_approval import ToolApprovalRequest
from app.models.user import User
from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.product import Product
from app.models.skill_package import (
    EmployeeSkillInstallation,
    EmployeeSkillInstallationStatus,
    SkillPackage,
    SkillPackageStatus,
)
from app.models.tenant import Tenant
from app.services import agent_tool_governance, edition_lifecycle_service, edition_service, license_service, skill_marketplace_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint

PROVIDER_STATE = Path("/tmp/w16-skill-provider-last.json")
PROVIDER_HEALTH = "http://127.0.0.1:18181/health"
TOOL = "workforce_execute_installed_skill"


async def prepare() -> tuple[list[str], uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    suffix = str(time.time_ns())[-12:]
    slug_vendor = f"w16-skill-vendor-{suffix}"
    slug_reseller = f"w16-skill-reseller-{suffix}"
    slug_a = f"w16-skill-exec-a-{suffix}"
    slug_b = f"w16-skill-exec-b-{suffix}"
    async with AsyncSessionLocal() as db:
        vendor = Tenant(name=f"W16 Skill Vendor {suffix}", slug=slug_vendor, status="active", tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor)
        await db.flush()
        reseller = Tenant(name=f"W16 Skill Reseller {suffix}", slug=slug_reseller, status="active", tenant_kind=edition_service.EDITION_RESELLER, parent_tenant_id=vendor.id)
        db.add(reseller)
        await db.flush()
        tenant_a = Tenant(name="W16 Skill Provider A", slug=slug_a, status="active", tenant_kind=edition_service.EDITION_CUSTOMER, parent_tenant_id=reseller.id)
        tenant_b = Tenant(name="W16 Skill Provider B", slug=slug_b, status="active")
        db.add_all([tenant_a, tenant_b])
        await db.flush()

        owner = User(tenant_id=tenant_a.id, email=f"w16-owner-{suffix}@example.invalid", password_hash="certification-fixture", full_name="W16 Skill Owner", is_active=True)
        reviewer = User(tenant_id=tenant_a.id, email=f"w16-reviewer-{suffix}@example.invalid", password_hash="certification-fixture", full_name="W16 Skill Reviewer", is_active=True)
        db.add_all([owner, reviewer])
        await db.flush()
        await license_service.issue_license(
            db,
            issuer=reseller,
            tenant=tenant_a,
            feature_codes=["employee.run", "tool:workforce_execute_installed_skill"],
            metadata={"certification_fixture": True, "purpose": "w16-skill-provider-execution"},
        )

        employee_a = Employee(
            tenant_id=tenant_a.id,
            slug=f"w16-skill-exec-employee-{suffix}",
            name="W16 Skill Execution Employee",
            kind="custom",
            is_active=True,
        )
        db.add(employee_a)
        await db.flush()
        allowed = ["workforce_execute_installed_skill"]
        version = EmployeeVersion(employee_id=employee_a.id, version_number=1, is_current=True, input_schema={}, output_schema={}, prompt_template="W16 Skill Provider Certification", allowed_tools=allowed, rules={})
        definition = AgentDefinition(tenant_id=tenant_a.id, slug=f"w16-skill-def-{suffix}", name="W16 Skill Definition", capabilities=["execution"], allowed_tools=allowed, model_policy={}, input_schema={}, output_schema={}, policy_requirements={}, enabled=True)
        db.add_all([version, definition])
        await db.flush()
        permission_policy = {"permissions": ["run.execute"], "allowed_tools": allowed}
        template = AgentTemplate(tenant_id=tenant_a.id, agent_definition_id=definition.id, slug=f"w16-skill-template-{suffix}", name="W16 Skill Template", version=1, status=AgentTemplateStatus.PUBLISHED, risk_tier=0, capability_contract={"execution": True}, permission_policy=permission_policy, approval_policy={}, evaluation_policy={"certification_fixture": True}, install_policy={}, published_at=datetime.now(timezone.utc))
        db.add(template)
        await db.flush()
        fingerprint = execution_authority_fingerprint(tenant_id=tenant_a.id, template_id=template.id, template_version=1, agent_definition_id=definition.id, risk_tier=0, capability_contract=template.capability_contract, permission_policy=permission_policy, approval_policy={}, install_policy={}, configuration={}, max_concurrency=1, budget_policy={})
        instance = AgentInstance(tenant_id=tenant_a.id, agent_definition_id=definition.id, agent_template_id=template.id, sponsor_user_id=owner.id, name="W16 Skill Instance", configuration={FINGERPRINT_KEY: fingerprint}, permission_policy=permission_policy, approval_policy={}, risk_tier=0, max_concurrency=1, budget_policy={}, enabled=True)
        db.add(instance)
        await db.flush()
        identity = AgentIdentity(tenant_id=tenant_a.id, agent_instance_id=instance.id, owner_user_id=owner.id, sponsor_user_id=owner.id, subject=f"agent:{tenant_a.id}:{instance.id}", active=True)
        db.add(identity)
        await db.flush()
        db.add(AgentAccessReview(tenant_id=tenant_a.id, agent_identity_id=identity.id, reviewer_user_id=reviewer.id, decision=AgentAccessReviewDecision.APPROVED, reason="Controlled W16 certification"))
        db.add(AgentRuntimeBinding(tenant_id=tenant_a.id, agent_definition_id=definition.id, employee_version_id=version.id, is_active=True))
        run = Run(tenant_id=tenant_a.id, employee_id=employee_a.id, employee_version_id=version.id, agent_instance_id=instance.id, created_by=owner.id, status="pending", input_data={"purpose": "W16 skill provider execution"})
        db.add(run)
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
            actor_id=owner.id,
        )
        installation = await skill_marketplace_service.install(
            db,
            tenant_id=tenant_a.id,
            employee_id=employee_a.id,
            skill_package_id=package.id,
        )
        assert installation.status == EmployeeSkillInstallationStatus.ACTIVE
        await db.commit()
        return [slug_vendor, slug_reseller, slug_a, slug_b], tenant_a.id, tenant_b.id, employee_a.id, instance.id, run.id, owner.id, reviewer.id


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
                source_owner_tenant_id=tenant_id,
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
    slugs, tenant_a_id, tenant_b_id, employee_a_id, instance_id, run_id, owner_id, reviewer_id = await prepare()
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

            approved_arguments = {
                "skill_package_id": str(package.id),
                "input": {"message": "hello", "count": 3},
            }
            db.add(ToolApprovalRequest(
                tenant_id=tenant_a_id,
                run_id=run_id,
                tool_name=TOOL,
                tool_call_id=request_id,
                arguments=approved_arguments,
                continuation_messages=[],
                iteration=0,
                status="approved",
                requested_by=owner_id,
                decided_by=reviewer_id,
                decision_reason="Controlled W16 provider execution fixture",
                decided_at=datetime.now(timezone.utc),
            ))
            await db.flush()

            try:
                async with agent_tool_governance.agent_tool_context(tenant_id=tenant_a_id, agent_instance_id=instance_id, run_id=run_id):
                    await registry.execute(
                        TOOL,
                        {"skill_package_id": str(package.id), "input": {}},
                        permissions={"run.execute"},
                        allowed_tools={TOOL},
                        db=db,
                        tenant_id=tenant_a_id,
                        agent_instance_id=instance_id,
                        employee_id=employee_a_id,
                        approval_granted=False,
                        tool_call_id=request_id,
                    )
            except ValidationAppError as exc:
                assert "Human approval required" in str(exc)
                print("SKILL PROVIDER EXECUTION APPROVAL GATE PASS")
            else:
                raise AssertionError("unapproved skill provider execution was accepted")

            async with agent_tool_governance.agent_tool_context(tenant_id=tenant_a_id, agent_instance_id=instance_id, run_id=run_id):
                result = await registry.execute(
                    TOOL,
                    approved_arguments,
                    permissions={"run.execute"},
                    allowed_tools={TOOL},
                    db=db,
                    tenant_id=tenant_a_id,
                    agent_instance_id=instance_id,
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
                async with agent_tool_governance.agent_tool_context(tenant_id=tenant_a_id, agent_instance_id=instance_id, run_id=run_id):
                    await registry.execute(
                        TOOL,
                        {"skill_package_id": str(package.id), "input": {}},
                        permissions={"run.execute"},
                        allowed_tools={TOOL},
                        db=db,
                        tenant_id=tenant_b_id,
                        agent_instance_id=instance_id,
                        employee_id=employee_a_id,
                        approval_granted=True,
                        tool_call_id=str(uuid.uuid4()),
                    )
            except ValidationAppError as exc:
                assert "tenant context mismatch" in str(exc)
                print("SKILL PROVIDER CROSS-TENANT REJECT PASS")
            else:
                raise AssertionError("cross-tenant skill execution was accepted")

        commercial_package_id = await prepare_commercial(tenant_a_id, employee_a_id)

        async with AsyncSessionLocal() as db:
            commercial_call_id = str(uuid.uuid4())
            commercial_arguments = {"skill_package_id": str(commercial_package_id), "input": {}}
            db.add(ToolApprovalRequest(
                tenant_id=tenant_a_id,
                run_id=run_id,
                tool_name=TOOL,
                tool_call_id=commercial_call_id,
                arguments=commercial_arguments,
                continuation_messages=[],
                iteration=0,
                status="approved",
                requested_by=owner_id,
                decided_by=reviewer_id,
                decision_reason="Controlled W16 commercial entitlement denial fixture",
                decided_at=datetime.now(timezone.utc),
            ))
            await db.flush()
            try:
                async with agent_tool_governance.agent_tool_context(tenant_id=tenant_a_id, agent_instance_id=instance_id, run_id=run_id):
                    await registry.execute(
                        TOOL,
                        commercial_arguments,
                        permissions={"run.execute"},
                        allowed_tools={TOOL},
                        db=db,
                        tenant_id=tenant_a_id,
                        agent_instance_id=instance_id,
                        employee_id=employee_a_id,
                        approval_granted=True,
                        tool_call_id=commercial_call_id,
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

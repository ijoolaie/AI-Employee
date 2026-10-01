"""Real-stack W4 Social/Instagram governance certification.

This certifies the governed Social Employee boundary, not live Instagram
publishing. The provider remains explicitly not_configured; an approved
publish proposal must stop at the provider boundary without external execution.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.agent_instance import AgentInstance
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.models.tool_approval import ToolApprovalRequest
from app.models.user import User
from app.models.tenant import Tenant
from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.services import agent_tool_governance, edition_service, license_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint
from app.ai.tool_registry import registry
from app.services.workforce_semantic_domains import _read_json

SOCIAL_TOOLS = [
    "workforce_read_comments",
    "workforce_triage_comments",
    "workforce_read_analytics",
    "workforce_publication_status",
    "workforce_connect_channel",
    "workforce_publish_post",
    "workforce_publish_reel",
    "workforce_publish_story",
    "workforce_schedule_publication",
    "workforce_respond_to_dm",
]


async def prepare():
    suffix = f"{os.environ.get('GITHUB_RUN_ID', 'local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor = Tenant(name=f"W4 Cert Vendor {suffix}", slug=f"w4-cert-vendor-{suffix}", status="active", tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor); await db.flush()
        reseller = Tenant(name=f"W4 Cert Reseller {suffix}", slug=f"w4-cert-reseller-{suffix}", status="active", tenant_kind=edition_service.EDITION_RESELLER, parent_tenant_id=vendor.id)
        db.add(reseller); await db.flush()
        customer = Tenant(name=f"W4 Cert Customer {suffix}", slug=f"w4-cert-customer-{suffix}", status="active", tenant_kind=edition_service.EDITION_CUSTOMER, parent_tenant_id=reseller.id)
        db.add(customer); await db.flush()
        owner = User(tenant_id=customer.id, email=f"w4-owner-{suffix}@example.invalid", password_hash="certification-fixture", full_name="W4 Certification Owner", is_active=True)
        reviewer = User(tenant_id=customer.id, email=f"w4-reviewer-{suffix}@example.invalid", password_hash="certification-fixture", full_name="W4 Certification Reviewer", is_active=True)
        db.add_all([owner, reviewer]); await db.flush()
        await license_service.issue_license(
            db, issuer=reseller, tenant=customer,
            feature_codes=["employee.run"] + [f"tool:{x}" for x in SOCIAL_TOOLS],
            metadata={"certification_fixture": True, "purpose": "W4-social-governance-e2e"},
        )
        employee = Employee(tenant_id=customer.id, slug=f"w4-social-{suffix}", name="W4 Social Employee", kind="custom", is_active=True)
        db.add(employee); await db.flush()
        version = EmployeeVersion(employee_id=employee.id, version_number=1, is_current=True, input_schema={}, output_schema={}, prompt_template="W4 Social Certification", allowed_tools=SOCIAL_TOOLS, rules={})
        definition = AgentDefinition(tenant_id=customer.id, slug=f"w4-social-def-{suffix}", name="W4 Social Definition", capabilities=["execution"], allowed_tools=SOCIAL_TOOLS, model_policy={}, input_schema={}, output_schema={}, policy_requirements={}, enabled=True)
        db.add_all([version, definition]); await db.flush()
        permission_policy = {"permissions": ["run.execute"], "allowed_tools": SOCIAL_TOOLS}
        template = AgentTemplate(tenant_id=customer.id, agent_definition_id=definition.id, slug=f"w4-social-template-{suffix}", name="W4 Social Template", version=1, status=AgentTemplateStatus.PUBLISHED, risk_tier=0, capability_contract={"execution": True}, permission_policy=permission_policy, approval_policy={}, evaluation_policy={"certification_fixture": True}, install_policy={}, published_at=datetime.now(timezone.utc))
        db.add(template); await db.flush()
        fingerprint = execution_authority_fingerprint(
            tenant_id=customer.id, template_id=template.id, template_version=template.version,
            agent_definition_id=definition.id, risk_tier=template.risk_tier,
            capability_contract=template.capability_contract, permission_policy=permission_policy,
            approval_policy=template.approval_policy, install_policy=template.install_policy,
            configuration={}, max_concurrency=1, budget_policy={},
        )
        instance = AgentInstance(tenant_id=customer.id, agent_definition_id=definition.id, agent_template_id=template.id, sponsor_user_id=owner.id, name="W4 Social Instance", configuration={FINGERPRINT_KEY: fingerprint}, permission_policy=permission_policy, approval_policy={}, risk_tier=0, max_concurrency=1, budget_policy={}, enabled=True)
        db.add(instance); await db.flush()
        identity = AgentIdentity(tenant_id=customer.id, agent_instance_id=instance.id, owner_user_id=owner.id, sponsor_user_id=owner.id, subject=f"agent:{customer.id}:{instance.id}", active=True)
        db.add(identity); await db.flush()
        db.add(AgentAccessReview(tenant_id=customer.id, agent_identity_id=identity.id, reviewer_user_id=reviewer.id, decision=AgentAccessReviewDecision.APPROVED, reason="Controlled W4 certification"))
        db.add(AgentRuntimeBinding(tenant_id=customer.id, agent_definition_id=definition.id, employee_version_id=version.id, is_active=True))
        read_run = Run(tenant_id=customer.id, employee_id=employee.id, employee_version_id=version.id, agent_instance_id=instance.id, created_by=owner.id, status="pending", input_data={"purpose":"W4 read boundary certification"})
        publish_run = Run(tenant_id=customer.id, employee_id=employee.id, employee_version_id=version.id, agent_instance_id=instance.id, created_by=owner.id, status="pending", input_data={"purpose":"W4 approved publish proposal certification"})
        db.add_all([read_run, publish_run]); await db.flush()
        publish_args = {"channel": "instagram", "content_id": "w4-cert-content", "provider": "instagram"}
        approval = ToolApprovalRequest(
            tenant_id=customer.id, run_id=publish_run.id, tool_name="workforce_publish_post",
            tool_call_id=f"w4-publish-{uuid.uuid4().hex}", arguments=publish_args,
            continuation_messages=[], iteration=0, status="approved",
            requested_by=owner.id, decided_by=reviewer.id,
            decision_reason="Controlled W4 certification; provider must remain fail-closed",
            decided_at=datetime.now(timezone.utc),
        )
        db.add(approval); await db.commit()
        return customer.id, instance.id, read_run.id, publish_run.id, approval.tool_call_id


async def execute(tenant_id, instance_id, run_id, tool_name, arguments, tool_call_id=None):
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(
            tenant_id=tenant_id, agent_instance_id=instance_id, run_id=run_id
        ):
            result = await registry.execute(
                tool_name, arguments, permissions={"run.execute"}, db=db,
                tenant_id=tenant_id, agent_instance_id=instance_id,
                tool_call_id=tool_call_id,
            )
        await db.commit()
        return result


async def main():
    tenant_id, instance_id, read_run, publish_run, publish_call_id = await prepare()

    read_result = await execute(
        tenant_id, instance_id, read_run, "workforce_read_comments",
        {"channel": "instagram"},
    )
    assert read_result["provider_execution"] == "not_configured", read_result
    assert read_result["external_side_effect"] is False, read_result
    assert read_result["approval_required"] is False, read_result
    assert read_result["storage_key"].startswith(f"{tenant_id}/")
    read_payload = _read_json(str(tenant_id), read_result["storage_key"])
    assert read_payload["provenance"]["tenant_id"] == str(tenant_id)

    publish_result = await execute(
        tenant_id, instance_id, publish_run, "workforce_publish_post",
        {"channel": "instagram", "content_id": "w4-cert-content", "provider": "instagram"},
        publish_call_id,
    )
    assert publish_result["approval_required"] is True, publish_result
    assert publish_result["approval_status"] == "pending", publish_result
    assert publish_result["external_side_effect"] is True, publish_result
    assert publish_result["provider_execution"] == "not_configured", publish_result
    assert publish_result["status"] == "proposal", publish_result
    publish_payload = _read_json(str(tenant_id), publish_result["storage_key"])
    assert publish_payload["provider_execution"] == "not_configured"
    assert publish_payload["approval_status"] == "pending"
    try:
        _read_json(str(uuid.uuid4()), publish_result["storage_key"])
    except Exception:
        pass
    else:
        raise AssertionError("W4 cross-tenant social artifact read unexpectedly succeeded")

    print("W4 SOCIAL EMPLOYEE GOVERNED READ RUN PASS")
    print(f"W4 SOCIAL ARTIFACT PASS social_id={read_result['social_id']}")
    print("W4 APPROVED PUBLISH PROPOSAL GOVERNANCE PASS")
    print(f"W4 PUBLISH PROPOSAL PASS social_id={publish_result['social_id']}")
    print("W4 PROVENANCE AND TENANT ISOLATION PASS")
    print("W4 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("WORKFORCE W4 SOCIAL GOVERNANCE REAL-STACK E2E PASS")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"WORKFORCE W4 SOCIAL GOVERNANCE REAL-STACK E2E FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

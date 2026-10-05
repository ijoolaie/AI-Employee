"""Real-stack W22 SEO & Growth Employee governance evidence.

This verifies the existing W7 semantic workforce foundation on PostgreSQL.
It does not claim live search-engine execution or SEO outcome impact.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.ai.tool_registry import registry
from app.core.database import AsyncSessionLocal
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.tool_approval import ToolApprovalRequest
from app.models.user import User
from app.services import agent_tool_governance, edition_service, license_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint
from app.services.workforce_semantic_domains import _read_json

TOOLS = [
    "workforce_keyword_research",
    "workforce_content_opportunity_analysis",
    "workforce_on_page_recommendations",
    "workforce_technical_seo_check",
    "workforce_internal_link_recommendations",
    "workforce_content_brief",
    "workforce_search_performance_ingestion",
    "workforce_growth_report",
    "workforce_seo_experiment_proposal",
]


async def prepare():
    suffix = f"{os.environ.get('GITHUB_RUN_ID', 'local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor = Tenant(name=f"W22 SEO Vendor {suffix}", slug=f"w22-seo-vendor-{suffix}", status="active", tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor)
        await db.flush()
        customer = Tenant(name=f"W22 SEO Customer {suffix}", slug=f"w22-seo-customer-{suffix}", status="active", tenant_kind=edition_service.EDITION_CUSTOMER, parent_tenant_id=vendor.id)
        db.add(customer)
        await db.flush()

        owner = User(tenant_id=customer.id, email=f"w22-owner-{suffix}@example.invalid", password_hash="fixture", full_name="W22 SEO Owner", is_active=True)
        reviewer = User(tenant_id=customer.id, email=f"w22-reviewer-{suffix}@example.invalid", password_hash="fixture", full_name="W22 SEO Reviewer", is_active=True)
        db.add_all([owner, reviewer])
        await db.flush()

        await license_service.issue_license(
            db,
            issuer=vendor,
            tenant=customer,
            feature_codes=["employee.run"] + [f"tool:{tool}" for tool in TOOLS],
            metadata={"certification_fixture": True, "purpose": "W22-seo-growth-e2e"},
        )

        employee = Employee(tenant_id=customer.id, slug=f"w22-seo-{suffix}", name="W22 SEO Employee", kind="custom", is_active=True)
        db.add(employee)
        await db.flush()
        version = EmployeeVersion(
            employee_id=employee.id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="W22 SEO Growth Certification",
            allowed_tools=TOOLS,
            rules={},
        )
        definition = AgentDefinition(
            tenant_id=customer.id,
            slug=f"w22-seo-def-{suffix}",
            name="W22 SEO Definition",
            capabilities=["execution"],
            allowed_tools=TOOLS,
            model_policy={},
            input_schema={},
            output_schema={},
            policy_requirements={},
            enabled=True,
        )
        db.add_all([version, definition])
        await db.flush()

        permission_policy = {"permissions": ["run.execute"], "allowed_tools": TOOLS}
        template = AgentTemplate(
            tenant_id=customer.id,
            agent_definition_id=definition.id,
            slug=f"w22-seo-template-{suffix}",
            name="W22 SEO Template",
            version=1,
            status=AgentTemplateStatus.PUBLISHED,
            risk_tier=0,
            capability_contract={"execution": True},
            permission_policy=permission_policy,
            approval_policy={},
            evaluation_policy={"certification_fixture": True},
            install_policy={},
            published_at=datetime.now(timezone.utc),
        )
        db.add(template)
        await db.flush()

        fingerprint = execution_authority_fingerprint(
            tenant_id=customer.id,
            template_id=template.id,
            template_version=1,
            agent_definition_id=definition.id,
            risk_tier=0,
            capability_contract=template.capability_contract,
            permission_policy=permission_policy,
            approval_policy={},
            install_policy={},
            configuration={},
            max_concurrency=1,
            budget_policy={},
        )
        instance = AgentInstance(
            tenant_id=customer.id,
            agent_definition_id=definition.id,
            agent_template_id=template.id,
            sponsor_user_id=owner.id,
            name="W22 SEO Instance",
            configuration={FINGERPRINT_KEY: fingerprint},
            permission_policy=permission_policy,
            approval_policy={},
            risk_tier=0,
            max_concurrency=1,
            budget_policy={},
            enabled=True,
        )
        db.add(instance)
        await db.flush()

        identity = AgentIdentity(
            tenant_id=customer.id,
            agent_instance_id=instance.id,
            owner_user_id=owner.id,
            sponsor_user_id=owner.id,
            subject=f"agent:{customer.id}:{instance.id}",
            active=True,
        )
        db.add(identity)
        await db.flush()
        db.add(AgentAccessReview(
            tenant_id=customer.id,
            agent_identity_id=identity.id,
            reviewer_user_id=reviewer.id,
            decision=AgentAccessReviewDecision.APPROVED,
            reason="Controlled W22 SEO certification",
        ))
        db.add(AgentRuntimeBinding(
            tenant_id=customer.id,
            agent_definition_id=definition.id,
            employee_version_id=version.id,
            is_active=True,
        ))

        research_run = Run(
            tenant_id=customer.id,
            employee_id=employee.id,
            employee_version_id=version.id,
            agent_instance_id=instance.id,
            created_by=owner.id,
            status="pending",
            input_data={"purpose": "W22 SEO research certification"},
        )
        proposal_run = Run(
            tenant_id=customer.id,
            employee_id=employee.id,
            employee_version_id=version.id,
            agent_instance_id=instance.id,
            created_by=owner.id,
            status="pending",
            input_data={"purpose": "W22 SEO experiment proposal certification"},
        )
        db.add_all([research_run, proposal_run])
        await db.flush()

        approval = ToolApprovalRequest(
            tenant_id=customer.id,
            run_id=proposal_run.id,
            tool_name="workforce_seo_experiment_proposal",
            tool_call_id=f"w22-seo-proposal-{uuid.uuid4().hex}",
            arguments={"topic": "governed SEO experiment"},
            continuation_messages=[],
            iteration=0,
            status="approved",
            requested_by=owner.id,
            decided_by=reviewer.id,
            decision_reason="Controlled W22 certification; no external provider execution",
            decided_at=datetime.now(timezone.utc),
        )
        db.add(approval)
        await db.commit()
        return customer.id, instance.id, research_run.id, proposal_run.id, approval.tool_call_id


async def execute(tenant_id, instance_id, run_id, tool_name, arguments, tool_call_id=None):
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(
            tenant_id=tenant_id,
            agent_instance_id=instance_id,
            run_id=run_id,
        ):
            result = await registry.execute(
                tool_name,
                arguments,
                permissions={"run.execute"},
                db=db,
                tenant_id=tenant_id,
                agent_instance_id=instance_id,
                tool_call_id=tool_call_id,
            )
        await db.commit()
        return result


async def main():
    tenant_id, instance_id, research_run, proposal_run, proposal_call_id = await prepare()

    operations = [
        "workforce_keyword_research",
        "workforce_content_opportunity_analysis",
        "workforce_on_page_recommendations",
        "workforce_technical_seo_check",
        "workforce_internal_link_recommendations",
        "workforce_content_brief",
        "workforce_search_performance_ingestion",
        "workforce_growth_report",
    ]
    artifacts = []
    for tool in operations:
        result = await execute(
            tenant_id,
            instance_id,
            research_run,
            tool,
            {"topic": "AI workforce SaaS", "query": "AI workforce SaaS", "recommendations": ["improve intent coverage"]},
        )
        assert result["provider_execution"] == "not_configured"
        assert result["external_side_effect"] is False
        assert result["storage_key"].startswith(f"{tenant_id}/")
        payload = _read_json(str(tenant_id), result["storage_key"])
        assert payload["provenance"]["tenant_id"] == str(tenant_id)
        artifacts.append(result["artifact_id"])

    proposal = await execute(
        tenant_id,
        instance_id,
        proposal_run,
        "workforce_seo_experiment_proposal",
        {"topic": "AI workforce SaaS", "spec": {"hypothesis": "improve organic discovery"}},
        proposal_call_id,
    )
    assert proposal["approval_required"] is True
    assert proposal["approval_status"] == "pending"
    assert proposal["external_side_effect"] is True
    assert proposal["provider_execution"] == "not_configured"
    assert proposal["status"] == "proposal"

    try:
        _read_json(str(uuid.uuid4()), proposal["storage_key"])
    except Exception:
        pass
    else:
        raise AssertionError("W22 cross-tenant SEO artifact read unexpectedly succeeded")

    print("W22 SEO/GROWTH RESEARCH OPERATIONS PASS count=8")
    print(f"W22 SEO ARTIFACT PROVENANCE PASS artifacts={len(artifacts)}")
    print("W22 APPROVAL-GATED EXPERIMENT PROPOSAL PASS")
    print("W22 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("W22 TENANT ISOLATION PASS")
    print("WORKFORCE W22 SEO GROWTH REAL-STACK E2E PASS")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"WORKFORCE W22 SEO GROWTH REAL-STACK E2E FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

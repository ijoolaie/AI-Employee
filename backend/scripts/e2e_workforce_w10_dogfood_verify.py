"""Real-stack W10 internal-company dogfood certification.

This certifies a repeatable governed revenue-workflow foundation using the
existing first-party workforce tools. It deliberately stops before any real
external outreach because the CRM/outreach provider is not configured.
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

TOOLS = [
    "workforce_lead_research",
    "workforce_lead_qualification",
    "workforce_prepare_content_brief",
    "workforce_produce_article",
    "workforce_content_qa",
    "workforce_prepare_outreach_draft",
    "workforce_external_outreach",
]


async def prepare():
    suffix = f"{os.environ.get('GITHUB_RUN_ID', 'local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor = Tenant(
            name=f"W10 Dogfood Vendor {suffix}",
            slug=f"w10-dogfood-vendor-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_VENDOR,
        )
        db.add(vendor)
        await db.flush()
        reseller = Tenant(
            name=f"W10 Dogfood Reseller {suffix}",
            slug=f"w10-dogfood-reseller-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_RESELLER,
            parent_tenant_id=vendor.id,
        )
        db.add(reseller)
        await db.flush()
        customer = Tenant(
            name=f"W10 Dogfood Customer {suffix}",
            slug=f"w10-dogfood-customer-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_CUSTOMER,
            parent_tenant_id=reseller.id,
        )
        db.add(customer)
        await db.flush()

        owner = User(
            tenant_id=customer.id,
            email=f"w10-owner-{suffix}@example.invalid",
            password_hash="certification-fixture",
            full_name="W10 Dogfood Owner",
            is_active=True,
        )
        reviewer = User(
            tenant_id=customer.id,
            email=f"w10-reviewer-{suffix}@example.invalid",
            password_hash="certification-fixture",
            full_name="W10 Dogfood Reviewer",
            is_active=True,
        )
        db.add_all([owner, reviewer])
        await db.flush()

        await license_service.issue_license(
            db,
            issuer=reseller,
            tenant=customer,
            feature_codes=["employee.run"] + [f"tool:{x}" for x in TOOLS],
            metadata={"certification_fixture": True, "purpose": "W10-internal-company-dogfood"},
        )

        employee = Employee(
            tenant_id=customer.id,
            slug=f"w10-revenue-workforce-{suffix}",
            name="W10 Revenue Workforce",
            kind="custom",
            is_active=True,
        )
        db.add(employee)
        await db.flush()

        version = EmployeeVersion(
            employee_id=employee.id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="W10 governed internal revenue workflow certification",
            allowed_tools=TOOLS,
            rules={"dogfood": True},
        )
        definition = AgentDefinition(
            tenant_id=customer.id,
            slug=f"w10-revenue-def-{suffix}",
            name="W10 Revenue Workforce Definition",
            capabilities=["execution", "revenue_workflow"],
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
            slug=f"w10-revenue-template-{suffix}",
            name="W10 Revenue Workforce Template",
            version=1,
            status=AgentTemplateStatus.PUBLISHED,
            risk_tier=0,
            capability_contract={"execution": True, "revenue_workflow": True},
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
            name="W10 Revenue Workforce Instance",
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
        db.add(
            AgentAccessReview(
                tenant_id=customer.id,
                agent_identity_id=identity.id,
                reviewer_user_id=reviewer.id,
                decision=AgentAccessReviewDecision.APPROVED,
                reason="Controlled W10 internal-company dogfood",
            )
        )
        db.add(
            AgentRuntimeBinding(
                tenant_id=customer.id,
                agent_definition_id=definition.id,
                employee_version_id=version.id,
                is_active=True,
            )
        )

        runs = {}
        for stage in ("lead_research", "lead_qualification", "content_brief", "article", "content_qa", "outreach_draft", "external_outreach"):
            run = Run(
                tenant_id=customer.id,
                employee_id=employee.id,
                employee_version_id=version.id,
                agent_instance_id=instance.id,
                created_by=owner.id,
                status="pending",
                input_data={"purpose": f"W10 dogfood stage: {stage}"},
            )
            db.add(run)
            await db.flush()
            runs[stage] = run.id

        outreach_args = {
            "query": "B2B SaaS founders with manual customer operations",
            "criteria": {"company_size": "10-200", "pain": "manual customer operations"},
            "message": "We can show a governed AI workforce workflow for customer operations.",
        }
        approval = ToolApprovalRequest(
            tenant_id=customer.id,
            run_id=runs["external_outreach"],
            tool_name="workforce_external_outreach",
            tool_call_id=f"w10-outreach-{uuid.uuid4().hex}",
            arguments=outreach_args,
            continuation_messages=[],
            iteration=0,
            status="approved",
            requested_by=owner.id,
            decided_by=reviewer.id,
            decision_reason="W10 dogfood: provider must remain fail-closed",
            decided_at=datetime.now(timezone.utc),
        )
        db.add(approval)
        await db.commit()
        return customer.id, instance.id, runs, approval.tool_call_id


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
    tenant_id, instance_id, runs, outreach_call_id = await prepare()

    lead_query = "B2B SaaS founders with manual customer operations"
    criteria = {"company_size": "10-200", "pain": "manual customer operations"}

    research = await execute(
        tenant_id, instance_id, runs["lead_research"],
        "workforce_lead_research", {"query": lead_query},
    )
    assert research["provider_execution"] == "not_configured"
    assert research["external_side_effect"] is False

    qualification = await execute(
        tenant_id, instance_id, runs["lead_qualification"],
        "workforce_lead_qualification", {"query": lead_query, "criteria": criteria},
    )
    assert qualification["provider_execution"] == "not_configured"
    assert qualification["external_side_effect"] is False

    brief = await execute(
        tenant_id, instance_id, runs["content_brief"],
        "workforce_prepare_content_brief",
        {"title": "AI workforce for manual customer operations", "body": "Governed workflow brief", "metadata": {"lead_query": lead_query}},
    )
    assert brief["provider_execution"] == "not_required"

    article = await execute(
        tenant_id, instance_id, runs["article"],
        "workforce_produce_article",
        {"title": "How governed AI workforces reduce manual customer operations", "body": "A certification fixture article.", "metadata": {"lead_query": lead_query}},
    )
    assert article["provider_execution"] == "not_required"

    qa = await execute(
        tenant_id, instance_id, runs["content_qa"],
        "workforce_content_qa",
        {"title": article.get("content_id", "w10-article"), "body": "A certification fixture article.", "metadata": {"stage": "content_qa"}},
    )
    assert qa["provider_execution"] == "not_required"

    draft = await execute(
        tenant_id, instance_id, runs["outreach_draft"],
        "workforce_prepare_outreach_draft",
        {"query": lead_query, "criteria": criteria, "message": "We can show a governed AI workforce workflow for customer operations."},
    )
    assert draft["provider_execution"] == "not_configured"
    assert draft["external_side_effect"] is False

    outreach_args = {
        "query": lead_query,
        "criteria": criteria,
        "message": "We can show a governed AI workforce workflow for customer operations.",
        "subject": "Governed AI workforce for customer operations",
        "to": ["prospect@example.invalid"],
        "channel": "email",
    }
    outreach = await execute(
        tenant_id, instance_id, runs["external_outreach"],
        "workforce_external_outreach",
        outreach_args,
        outreach_call_id,
    )
    assert outreach["approval_required"] is True
    assert outreach["approval_status"] == "approved"
    assert outreach["status"] == "proposal"
    assert outreach["external_side_effect"] is True
    assert outreach["provider_execution"] == "not_configured"
    assert outreach["execution"]["executed"] is False

    print("W10 LEAD RESEARCH AND QUALIFICATION PASS")
    print(f"W10 SALES RESEARCH ID={research['sales_id']}")
    print(f"W10 QUALIFICATION ID={qualification['sales_id']}")
    print("W10 CONTENT BRIEF -> ARTICLE -> QA PASS")
    print(f"W10 CONTENT ARTICLE ID={article['content_id']}")
    print("W10 OUTREACH DRAFT PASS")
    print(f"W10 OUTREACH PROPOSAL ID={outreach['sales_id']}")
    print("W10 APPROVAL GOVERNANCE PASS")
    print("W10 EXTERNAL PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("W10 REVENUE WORKFLOW FOUNDATION REAL-STACK E2E PASS")
    print("W10 FULL REVENUE OUTCOME NOT_VERIFIED: external provider not configured")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"W10 REVENUE WORKFLOW FOUNDATION REAL-STACK E2E FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

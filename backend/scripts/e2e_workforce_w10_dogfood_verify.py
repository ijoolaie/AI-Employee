"""Real-stack W10 internal-company dogfood certification.

This certifies a repeatable governed revenue-workflow foundation using the
existing first-party workforce tools. Outbound delivery uses the isolated SMTP
sink and inbound response uses the operator-configured contract-test provider;
real customer delivery, response, and revenue remain outside this certification.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

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
from app.models.audit_log import AuditLog
from app.services import agent_tool_governance, edition_service, license_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint
from app.ai.tool_registry import registry
from app.services import workforce_sales_engagement

TOOLS = [
    "workforce_lead_research",
    "workforce_lead_qualification",
    "workforce_prepare_content_brief",
    "workforce_produce_article",
    "workforce_content_qa",
    "workforce_prepare_outreach_draft",
    "workforce_external_outreach",
    "create_deal",
    "sales_pipeline_summary",
    "sales_forecast",
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

        deal_args = {
            "title": "W10 qualified AI workforce opportunity",
            "customer_name": "Certification Prospect",
            "customer_email": "prospect@example.invalid",
            "amount": 250000000,
            "currency": "IRR",
            "stage": "qualified",
            "probability": 25,
            "source": "ai_workforce_dogfood",
            "notes": "Certification-only internal pipeline record.",
        }
        deal_approval = ToolApprovalRequest(
            tenant_id=customer.id,
            run_id=runs["outreach_draft"],
            tool_name="create_deal",
            tool_call_id=f"w10-deal-{uuid.uuid4().hex}",
            arguments=deal_args,
            continuation_messages=[],
            iteration=0,
            status="approved",
            requested_by=owner.id,
            decided_by=reviewer.id,
            decision_reason="W10 dogfood: governed internal CRM mutation",
            decided_at=datetime.now(timezone.utc),
        )
        db.add(deal_approval)

        await db.commit()
        return customer.id, instance.id, runs, owner.id, reviewer.id, deal_approval.tool_call_id


async def execute(tenant_id, instance_id, run_id, tool_name, arguments, tool_call_id=None, actor_id=None):
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
                actor_id=actor_id,
                agent_instance_id=instance_id,
                tool_call_id=tool_call_id,
            )
        await db.commit()
        return result


async def main():
    tenant_id, instance_id, runs, owner_id, reviewer_id, deal_approval_tool_call_id = await prepare()

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
    deal_args = {
        "title": "W10 qualified AI workforce opportunity",
        "customer_name": "Certification Prospect",
        "customer_email": "prospect@example.invalid",
        "amount": 250000000, "currency": "IRR", "stage": "qualified", "probability": 25,
        "source": "ai_workforce_dogfood",
        "notes": "Certification-only internal pipeline record.",
    }
    deal = await execute(
        tenant_id, instance_id, runs["outreach_draft"], "create_deal",
        deal_args,
        tool_call_id=deal_approval_tool_call_id,
    )
    pipeline = await execute(tenant_id, instance_id, runs["outreach_draft"], "sales_pipeline_summary", {})
    forecast = await execute(tenant_id, instance_id, runs["outreach_draft"], "sales_forecast", {"horizon_days": 30})
    if not deal.get("deal_id"):
        raise RuntimeError(f"W10 create_deal returned no deal_id: {deal!r}")
    if deal.get("stage") != "qualified":
        raise RuntimeError(f"W10 create_deal stage mismatch: {deal!r}")
    if pipeline.get("total_deals", 0) < 1:
        raise RuntimeError(f"W10 pipeline total_deals mismatch: {pipeline!r}")
    if pipeline.get("weighted_pipeline", 0) < 62500000.0:
        raise RuntimeError(f"W10 weighted_pipeline mismatch: {pipeline!r}")
    if forecast.get("expected_revenue", 0) < 62500000.0:
        raise RuntimeError(f"W10 forecast mismatch: {forecast!r}")

    outreach_args = {
        "query": lead_query,
        "criteria": criteria,
        "message": "We can show a governed AI workforce workflow for customer operations.",
        "subject": "Governed AI workforce for customer operations",
        "to": ["prospect@example.invalid"],
        "channel": "email",
        "deal_id": deal["deal_id"],
    }

    # The consequential outreach approval is created only after the governed
    # CRM mutation has produced the durable deal_id. This keeps the approved
    # argument set immutable and makes the delivery event fully attributable.
    outreach_call_id = f"w10-outreach-{uuid.uuid4().hex}"
    async with AsyncSessionLocal() as db:
        db.add(
            ToolApprovalRequest(
                tenant_id=tenant_id,
                run_id=runs["external_outreach"],
                tool_name="workforce_external_outreach",
                tool_call_id=outreach_call_id,
                arguments=outreach_args,
                continuation_messages=[],
                iteration=0,
                status="approved",
                requested_by=owner_id,
                decided_by=reviewer_id,
                decision_reason="W10 dogfood: approved outreach for governed attribution",
                decided_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()

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

    if os.environ.get("SALES_OUTREACH_PROVIDER_NAME", "none").strip().lower() == "smtp":
        assert outreach["provider_execution"] == "queued"
        assert outreach["execution"]["executed"] is True
        assert outreach["execution"]["queued"] is True
        print("W10 SMTP OUTREACH PROVIDER QUEUE PASS")
        delivery_event = None
        delivery_event_key = f"delivered:{outreach['execution']['outbox_id']}"
        for _ in range(30):
            async with AsyncSessionLocal() as db:
                delivery_event = (
                    await db.execute(
                        select(AuditLog).where(
                            AuditLog.tenant_id == tenant_id,
                            AuditLog.action == workforce_sales_engagement.EVENT_ACTION,
                            AuditLog.resource_type == "sales_engagement",
                            AuditLog.metadata_.op("->>")("event_key") == delivery_event_key,
                        )
                    )
                ).scalar_one_or_none()
                if delivery_event is not None:
                    metadata = delivery_event.metadata_ or {}
                    assert metadata.get("event_type") == "outreach_delivered"
                    assert metadata.get("outbox_id") == outreach["execution"]["outbox_id"]
                    assert metadata.get("tool_call_id") == outreach_call_id
                    assert metadata.get("deal_id") == deal["deal_id"]
                    break
            await asyncio.sleep(1)

        if delivery_event is None:
            raise RuntimeError(
                f"W10 delivery event not emitted by email worker: {delivery_event_key}"
            )

        print("W10 SALES DELIVERY EVENT INGESTION PASS")

        # Exercise the real application ingress path: provider adapter ->
        # authenticated webhook -> delivery correlation -> immutable ledger.
        response_event_id = f"w10-provider-response-{uuid.uuid4().hex}"
        provider_message_id = (delivery_event.metadata_ or {}).get("provider_message_id")
        assert provider_message_id
        inbound_secret = os.environ.get("SALES_INBOUND_CONTRACT_SECRET", "w10-contract-secret")
        inbound_body = json.dumps(
            {
                "provider_message_id": provider_message_id,
                "response_text": "Certification prospect replied: please send pricing and implementation details.",
            },
            separators=(",", ":"),
        ).encode("utf-8")
        inbound_signature = hmac.new(
            inbound_secret.encode("utf-8"),
            inbound_body,
            hashlib.sha256,
        ).hexdigest()
        inbound_url = (
            os.environ.get("SALES_INBOUND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
            + f"/api/v1/webhooks/sales/outreach/{tenant_id}"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            inbound_response = await client.post(
                inbound_url,
                content=inbound_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Sales-Event-Id": response_event_id,
                    "X-Sales-Provider-Message-Id": provider_message_id,
                    "X-Sales-Signature": inbound_signature,
                },
            )
            assert inbound_response.status_code == 202, inbound_response.text
            inbound_payload = inbound_response.json()
            assert inbound_payload["event_type"] == "outreach_response"
            assert inbound_payload["event_key"] == f"provider:contract-test:{response_event_id}"

            replay = await client.post(
                inbound_url,
                content=inbound_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Sales-Event-Id": response_event_id,
                    "X-Sales-Provider-Message-Id": provider_message_id,
                    "X-Sales-Signature": inbound_signature,
                },
            )
            assert replay.status_code == 202, replay.text
            replay_payload = replay.json()
            assert replay_payload["event_id"] == inbound_payload["event_id"]

        print("W10 SALES PROVIDER INBOUND RESPONSE INGESTION PASS")

        async with AsyncSessionLocal() as db:
            summary = await workforce_sales_engagement.attribution_summary(
                db, tenant_id=tenant_id
            )
            assert summary["delivered"] == 1
            assert summary["responded"] == 1
            assert summary["event_count"] == 2
            foreign_summary = await workforce_sales_engagement.attribution_summary(
                db, tenant_id=uuid.uuid4(), deal_id=deal["deal_id"]
            )
            assert foreign_summary["event_count"] == 0
            assert foreign_summary["delivered"] == 0
            assert foreign_summary["responded"] == 0
            await db.commit()
        print("W10 SALES RESPONSE IDEMPOTENCY PASS")
        print("W10 SALES ATTRIBUTION PASS sent=1 delivered=1 responded=1")
        print("W10 SALES DELIVERY + RESPONSE INGESTION PASS")
        print("W10 SALES RESPONSE IDEMPOTENCY PASS")
        print("W10 SALES ATTRIBUTION PASS sent=1 delivered=1 responded=1")
    else:
        assert outreach["provider_execution"] == "not_configured"
        assert outreach["execution"]["executed"] is False
        print("W10 EXTERNAL PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")

    print("W10 LEAD RESEARCH AND QUALIFICATION PASS")
    print(f"W10 SALES RESEARCH ID={research['sales_id']}")
    print(f"W10 QUALIFICATION ID={qualification['sales_id']}")
    print("W10 CONTENT BRIEF -> ARTICLE -> QA PASS")
    print(f"W10 CONTENT ARTICLE ID={article['content_id']}")
    print("W10 INTERNAL CRM DEAL + PIPELINE + FORECAST PASS")
    print("W10 DEAL ID=" + deal["deal_id"])
    print("W10 WEIGHTED PIPELINE=" + str(pipeline["weighted_pipeline"]))
    print("W10 FORECAST=" + str(forecast["expected_revenue"]))
    print("W10 OUTREACH DRAFT PASS")
    print(f"W10 OUTREACH PROPOSAL ID={outreach['sales_id']}")
    print("W10 APPROVAL GOVERNANCE PASS")
    if os.environ.get("SALES_OUTREACH_PROVIDER_NAME", "none").strip().lower() != "smtp":
        print("W10 EXTERNAL PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("W10 REVENUE WORKFLOW FOUNDATION REAL-STACK E2E PASS")
    if os.environ.get("SALES_OUTREACH_PROVIDER_NAME", "none").strip().lower() == "smtp":
        print("W10 FULL REVENUE OUTCOME NOT_VERIFIED: E2E SMTP sink only; no real customer delivery or revenue claimed")
    else:
        print("W10 FULL REVENUE OUTCOME NOT_VERIFIED: external provider not configured")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        print(f"W10 REVENUE WORKFLOW FOUNDATION REAL-STACK E2E FAIL: {type(exc).__name__}: {exc!r}", file=sys.stderr)
        raise SystemExit(1)

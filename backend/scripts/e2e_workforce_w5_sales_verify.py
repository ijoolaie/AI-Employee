"""Real-stack W5 Sales & Lead Generation governance certification.

Verifies governed sales research and outreach-proposal runs, tenant-scoped
artifacts, approval state, provenance, and fail-closed CRM/outreach provider
boundary. No external outreach is executed.
"""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import datetime, timezone

PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)

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

SALES_TOOLS=[
"workforce_lead_research","workforce_lead_qualification","workforce_crm_enrichment",
"workforce_prepare_outreach_draft","workforce_prepare_follow_up_queue",
"workforce_prepare_proposal","workforce_prepare_meeting_request",
"workforce_pipeline_reporting","workforce_conversion_attribution",
"workforce_external_outreach","workforce_contractual_commitment",
"workforce_material_commercial_action",
]

async def prepare():
    suffix=f"{os.environ.get('GITHUB_RUN_ID','local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor=Tenant(name=f"W5 Cert Vendor {suffix}",slug=f"w5-cert-vendor-{suffix}",status="active",tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor); await db.flush()
        reseller=Tenant(name=f"W5 Cert Reseller {suffix}",slug=f"w5-cert-reseller-{suffix}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=vendor.id)
        db.add(reseller); await db.flush()
        customer=Tenant(name=f"W5 Cert Customer {suffix}",slug=f"w5-cert-customer-{suffix}",status="active",tenant_kind=edition_service.EDITION_CUSTOMER,parent_tenant_id=reseller.id)
        db.add(customer); await db.flush()
        owner=User(tenant_id=customer.id,email=f"w5-owner-{suffix}@example.invalid",password_hash="certification-fixture",full_name="W5 Certification Owner",is_active=True)
        reviewer=User(tenant_id=customer.id,email=f"w5-reviewer-{suffix}@example.invalid",password_hash="certification-fixture",full_name="W5 Certification Reviewer",is_active=True)
        db.add_all([owner,reviewer]); await db.flush()
        await license_service.issue_license(db,issuer=reseller,tenant=customer,feature_codes=["employee.run"]+[f"tool:{x}" for x in SALES_TOOLS],metadata={"certification_fixture":True,"purpose":"W5-sales-e2e"})
        employee=Employee(tenant_id=customer.id,slug=f"w5-sales-{suffix}",name="W5 Sales Employee",kind="custom",is_active=True)
        db.add(employee); await db.flush()
        version=EmployeeVersion(employee_id=employee.id,version_number=1,is_current=True,input_schema={},output_schema={},prompt_template="W5 Sales Certification",allowed_tools=SALES_TOOLS,rules={})
        definition=AgentDefinition(tenant_id=customer.id,slug=f"w5-sales-def-{suffix}",name="W5 Sales Definition",capabilities=["execution"],allowed_tools=SALES_TOOLS,model_policy={},input_schema={},output_schema={},policy_requirements={},enabled=True)
        db.add_all([version,definition]); await db.flush()
        permission_policy={"permissions":["run.execute"],"allowed_tools":SALES_TOOLS}
        template=AgentTemplate(tenant_id=customer.id,agent_definition_id=definition.id,slug=f"w5-sales-template-{suffix}",name="W5 Sales Template",version=1,status=AgentTemplateStatus.PUBLISHED,risk_tier=0,capability_contract={"execution":True},permission_policy=permission_policy,approval_policy={},evaluation_policy={"certification_fixture":True},install_policy={},published_at=datetime.now(timezone.utc))
        db.add(template); await db.flush()
        fingerprint=execution_authority_fingerprint(tenant_id=customer.id,template_id=template.id,template_version=template.version,agent_definition_id=definition.id,risk_tier=template.risk_tier,capability_contract=template.capability_contract,permission_policy=permission_policy,approval_policy=template.approval_policy,install_policy=template.install_policy,configuration={},max_concurrency=1,budget_policy={})
        instance=AgentInstance(tenant_id=customer.id,agent_definition_id=definition.id,agent_template_id=template.id,sponsor_user_id=owner.id,name="W5 Sales Instance",configuration={FINGERPRINT_KEY:fingerprint},permission_policy=permission_policy,approval_policy={},risk_tier=0,max_concurrency=1,budget_policy={},enabled=True)
        db.add(instance); await db.flush()
        identity=AgentIdentity(tenant_id=customer.id,agent_instance_id=instance.id,owner_user_id=owner.id,sponsor_user_id=owner.id,subject=f"agent:{customer.id}:{instance.id}",active=True)
        db.add(identity); await db.flush()
        db.add(AgentAccessReview(tenant_id=customer.id,agent_identity_id=identity.id,reviewer_user_id=reviewer.id,decision=AgentAccessReviewDecision.APPROVED,reason="Controlled W5 certification"))
        db.add(AgentRuntimeBinding(tenant_id=customer.id,agent_definition_id=definition.id,employee_version_id=version.id,is_active=True))
        research_run=Run(tenant_id=customer.id,employee_id=employee.id,employee_version_id=version.id,agent_instance_id=instance.id,created_by=owner.id,status="pending",input_data={"purpose":"W5 research certification"})
        outreach_run=Run(tenant_id=customer.id,employee_id=employee.id,employee_version_id=version.id,agent_instance_id=instance.id,created_by=owner.id,status="pending",input_data={"purpose":"W5 approved outreach proposal certification"})
        db.add_all([research_run,outreach_run]); await db.flush()
        args={"query":"B2B SaaS prospects","criteria":{"segment":"SMB"},"message":"W5 governed outreach proposal","provider":"crm_or_outreach"}
        approval=ToolApprovalRequest(tenant_id=customer.id,run_id=outreach_run.id,tool_name="workforce_external_outreach",tool_call_id=f"w5-outreach-{uuid.uuid4().hex}",arguments=args,continuation_messages=[],iteration=0,status="approved",requested_by=owner.id,decided_by=reviewer.id,decision_reason="Controlled W5 certification; provider must remain fail-closed",decided_at=datetime.now(timezone.utc))
        db.add(approval); await db.commit()
        return customer.id,instance.id,research_run.id,outreach_run.id,approval.tool_call_id

async def execute(tenant_id,instance_id,run_id,tool_name,arguments,tool_call_id=None):
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id,agent_instance_id=instance_id,run_id=run_id):
            result=await registry.execute(tool_name,arguments,permissions={"run.execute"},db=db,tenant_id=tenant_id,agent_instance_id=instance_id,tool_call_id=tool_call_id)
        await db.commit()
        return result

async def main():
    tenant_id,instance_id,research_run,outreach_run,call_id=await prepare()
    research=await execute(tenant_id,instance_id,research_run,"workforce_lead_research",{"query":"B2B SaaS prospects","criteria":{"segment":"SMB"}})
    assert research["provider_execution"]=="not_configured",research
    assert research["approval_required"] is False,research
    assert research["external_side_effect"] is False,research
    assert research["storage_key"].startswith(f"{tenant_id}/")
    payload=_read_json(str(tenant_id),research["storage_key"])
    assert payload["provenance"]["tenant_id"]==str(tenant_id)

    outreach=await execute(tenant_id,instance_id,outreach_run,"workforce_external_outreach",{"query":"B2B SaaS prospects","criteria":{"segment":"SMB"},"message":"W5 governed outreach proposal","provider":"crm_or_outreach"},call_id)
    assert outreach["approval_required"] is True,outreach
    assert outreach["approval_status"]=="pending",outreach
    assert outreach["status"]=="proposal",outreach
    assert outreach["external_side_effect"] is True,outreach
    assert outreach["provider_execution"]=="not_configured",outreach
    proposal=_read_json(str(tenant_id),outreach["storage_key"])
    assert proposal["provenance"]["tenant_id"]==str(tenant_id)
    assert proposal["approval_status"]=="pending"
    assert proposal["provider_execution"]=="not_configured"
    try: _read_json(str(uuid.uuid4()),outreach["storage_key"])
    except Exception: pass
    else: raise AssertionError("W5 cross-tenant sales artifact read unexpectedly succeeded")
    print("W5 SALES EMPLOYEE GOVERNED RESEARCH RUN PASS")
    print(f"W5 SALES ARTIFACT PASS sales_id={research['sales_id']}")
    print("W5 APPROVED OUTREACH PROPOSAL GOVERNANCE PASS")
    print(f"W5 OUTREACH PROPOSAL PASS sales_id={outreach['sales_id']}")
    print("W5 PROVENANCE AND TENANT ISOLATION PASS")
    print("W5 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("WORKFORCE W5 SALES REAL-STACK E2E PASS")

if __name__=="__main__":
    try: asyncio.run(main())
    except Exception as exc:
        print(f"WORKFORCE W5 SALES REAL-STACK E2E FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

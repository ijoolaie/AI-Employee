"""Real-stack W23 Customer Success & Support governance evidence."""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import datetime, timezone
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
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

TOOLS=[
"workforce_customer_context","workforce_support_triage","workforce_conversation_summary",
"workforce_churn_risk_evidence","workforce_escalation_recommendation","workforce_response_draft",
"workforce_customer_health_report","workforce_send_customer_message",
"workforce_account_change_proposal","workforce_refund_proposal","workforce_cancellation_proposal",
]

async def prepare():
    suffix=f"{os.environ.get('GITHUB_RUN_ID','local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor=Tenant(name=f"W23 Vendor {suffix}",slug=f"w23-vendor-{suffix}",status="active",tenant_kind=edition_service.EDITION_VENDOR); db.add(vendor); await db.flush()
        reseller=Tenant(name=f"W23 Reseller {suffix}",slug=f"w23-reseller-{suffix}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=vendor.id); db.add(reseller); await db.flush()
        customer=Tenant(name=f"W23 Customer {suffix}",slug=f"w23-customer-{suffix}",status="active",tenant_kind=edition_service.EDITION_CUSTOMER,parent_tenant_id=reseller.id); db.add(customer); await db.flush()
        owner=User(tenant_id=customer.id,email=f"w23-owner-{suffix}@example.invalid",password_hash="fixture",full_name="W23 Owner",is_active=True)
        reviewer=User(tenant_id=customer.id,email=f"w23-reviewer-{suffix}@example.invalid",password_hash="fixture",full_name="W23 Reviewer",is_active=True)
        db.add_all([owner,reviewer]); await db.flush()
        await license_service.issue_license(db,issuer=reseller,tenant=customer,feature_codes=["employee.run"]+[f"tool:{x}" for x in TOOLS],metadata={"certification_fixture":True,"purpose":"W23-customer-success-e2e"})
        employee=Employee(tenant_id=customer.id,slug=f"w23-cs-{suffix}",name="W23 Customer Success Employee",kind="custom",is_active=True); db.add(employee); await db.flush()
        version=EmployeeVersion(employee_id=employee.id,version_number=1,is_current=True,input_schema={},output_schema={},prompt_template="W23 Customer Success Certification",allowed_tools=TOOLS,rules={})
        definition=AgentDefinition(tenant_id=customer.id,slug=f"w23-cs-def-{suffix}",name="W23 Customer Success Definition",capabilities=["execution"],allowed_tools=TOOLS,model_policy={},input_schema={},output_schema={},policy_requirements={},enabled=True)
        db.add_all([version,definition]); await db.flush()
        policy={"permissions":["run.execute"],"allowed_tools":TOOLS}
        template=AgentTemplate(tenant_id=customer.id,agent_definition_id=definition.id,slug=f"w23-cs-template-{suffix}",name="W23 Customer Success Template",version=1,status=AgentTemplateStatus.PUBLISHED,risk_tier=0,capability_contract={"execution":True},permission_policy=policy,approval_policy={},evaluation_policy={"certification_fixture":True},install_policy={},published_at=datetime.now(timezone.utc)); db.add(template); await db.flush()
        fp=execution_authority_fingerprint(tenant_id=customer.id,template_id=template.id,template_version=1,agent_definition_id=definition.id,risk_tier=0,capability_contract=template.capability_contract,permission_policy=policy,approval_policy={},install_policy={},configuration={},max_concurrency=1,budget_policy={})
        instance=AgentInstance(tenant_id=customer.id,agent_definition_id=definition.id,agent_template_id=template.id,sponsor_user_id=owner.id,name="W23 Customer Success Instance",configuration={FINGERPRINT_KEY:fp},permission_policy=policy,approval_policy={},risk_tier=0,max_concurrency=1,budget_policy={},enabled=True); db.add(instance); await db.flush()
        identity=AgentIdentity(tenant_id=customer.id,agent_instance_id=instance.id,owner_user_id=owner.id,sponsor_user_id=owner.id,subject=f"agent:{customer.id}:{instance.id}",active=True); db.add(identity); await db.flush()
        db.add(AgentAccessReview(tenant_id=customer.id,agent_identity_id=identity.id,reviewer_user_id=reviewer.id,decision=AgentAccessReviewDecision.APPROVED,reason="Controlled W23 certification"))
        db.add(AgentRuntimeBinding(tenant_id=customer.id,agent_definition_id=definition.id,employee_version_id=version.id,is_active=True))
        routine_run=Run(tenant_id=customer.id,employee_id=employee.id,employee_version_id=version.id,agent_instance_id=instance.id,created_by=owner.id,status="pending",input_data={"purpose":"W23 routine evidence"})
        external_run=Run(tenant_id=customer.id,employee_id=employee.id,employee_version_id=version.id,agent_instance_id=instance.id,created_by=owner.id,status="pending",input_data={"purpose":"W23 customer message proposal"})
        db.add_all([routine_run,external_run]); await db.flush()
        args={"customer_reference":"fixture-customer","message":"Prepared support response for approval"}
        approval=ToolApprovalRequest(tenant_id=customer.id,run_id=external_run.id,tool_name="workforce_send_customer_message",tool_call_id=f"w23-message-{uuid.uuid4().hex}",arguments=args,continuation_messages=[],iteration=0,status="approved",requested_by=owner.id,decided_by=reviewer.id,decision_reason="Controlled W23 certification; provider remains fail-closed",decided_at=datetime.now(timezone.utc)); db.add(approval); await db.commit()
        return customer.id,instance.id,routine_run.id,external_run.id,approval.tool_call_id

async def execute(tenant_id,instance_id,run_id,tool_name,arguments,tool_call_id=None):
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id,agent_instance_id=instance_id,run_id=run_id):
            result=await registry.execute(tool_name,arguments,permissions={"run.execute"},db=db,tenant_id=tenant_id,agent_instance_id=instance_id,tool_call_id=tool_call_id)
        await db.commit(); return result

async def main():
    tenant_id,instance_id,routine_run,external_run,call_id=await prepare()
    tools=[
      "workforce_customer_context","workforce_support_triage","workforce_conversation_summary",
      "workforce_churn_risk_evidence","workforce_escalation_recommendation","workforce_response_draft",
      "workforce_customer_health_report",
    ]
    for tool in tools:
        result=await execute(tenant_id,instance_id,routine_run,tool,{"customer_reference":"fixture-customer","query":"support health evidence","recommendation":"review onboarding context","evidence":["fixture-evidence"]})
        assert result["provider_execution"]=="not_configured"
        assert result["external_side_effect"] is False
        assert result["storage_key"].startswith(f"{tenant_id}/")
        payload=_read_json(str(tenant_id),result["storage_key"])
        assert payload["provenance"]["tenant_id"]==str(tenant_id)
    args={"customer_reference":"fixture-customer","message":"Prepared support response for approval"}
    result=await execute(tenant_id,instance_id,external_run,"workforce_send_customer_message",args,call_id)
    assert result["approval_required"] is True
    assert result["external_side_effect"] is True
    assert result["provider_execution"]=="not_configured"
    assert result["status"]=="proposal"
    try: _read_json(str(uuid.uuid4()),result["storage_key"])
    except Exception: pass
    else: raise AssertionError("W23 cross-tenant customer-success artifact read unexpectedly succeeded")
    print("W23 CUSTOMER SUCCESS ROUTINE OPERATIONS PASS count=7")
    print("W23 CUSTOMER SUCCESS PROVENANCE PASS")
    print("W23 APPROVED CUSTOMER MESSAGE PROPOSAL PASS")
    print("W23 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("W23 TENANT ISOLATION PASS")
    print("WORKFORCE W23 CUSTOMER SUCCESS REAL-STACK E2E PASS")

if __name__=="__main__":
    try: asyncio.run(main())
    except Exception as exc:
        print(f"WORKFORCE W23 CUSTOMER SUCCESS REAL-STACK E2E FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

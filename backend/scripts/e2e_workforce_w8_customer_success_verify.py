"""W8 Customer Success & Support real-stack certification."""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import datetime, timezone
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
from app.core.database import AsyncSessionLocal
from app.models.agent_access_review import AgentAccessReview,AgentAccessReviewDecision
from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.agent_template import AgentTemplate,AgentTemplateStatus
from app.models.employee import Employee,EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.tool_approval import ToolApprovalRequest
from app.models.user import User
from app.services import agent_tool_governance,edition_service,license_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY,execution_authority_fingerprint
from app.ai.tool_registry import registry
from app.services.workforce_semantic_domains import _read_json
TOOLS=["workforce_customer_context","workforce_support_triage","workforce_conversation_summary","workforce_churn_risk_evidence","workforce_escalation_recommendation","workforce_response_draft","workforce_customer_health_report","workforce_send_customer_message","workforce_account_change_proposal","workforce_refund_proposal","workforce_cancellation_proposal"]

async def prepare():
 s=f"{os.environ.get('GITHUB_RUN_ID','local')}-{uuid.uuid4().hex[:8]}"
 async with AsyncSessionLocal() as db:
  v=Tenant(name=f"W8 Vendor {s}",slug=f"w8-vendor-{s}",status="active",tenant_kind=edition_service.EDITION_VENDOR);db.add(v);await db.flush()
  r=Tenant(name=f"W8 Reseller {s}",slug=f"w8-reseller-{s}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=v.id);db.add(r);await db.flush()
  t=Tenant(name=f"W8 Customer {s}",slug=f"w8-customer-{s}",status="active",tenant_kind=edition_service.EDITION_CUSTOMER,parent_tenant_id=r.id);db.add(t);await db.flush()
  o=User(tenant_id=t.id,email=f"w8-owner-{s}@example.invalid",password_hash="certification-fixture",full_name="W8 Owner",is_active=True)
  rv=User(tenant_id=t.id,email=f"w8-reviewer-{s}@example.invalid",password_hash="certification-fixture",full_name="W8 Reviewer",is_active=True);db.add_all([o,rv]);await db.flush()
  await license_service.issue_license(db,issuer=r,tenant=t,feature_codes=["employee.run"]+[f"tool:{x}" for x in TOOLS],metadata={"certification_fixture":True,"purpose":"W8-customer-success-e2e"})
  e=Employee(tenant_id=t.id,slug=f"w8-customer-success-{s}",name="W8 Customer Success Employee",kind="custom",is_active=True);db.add(e);await db.flush()
  ev=EmployeeVersion(employee_id=e.id,version_number=1,is_current=True,input_schema={},output_schema={},prompt_template="W8 Customer Success Certification",allowed_tools=TOOLS,rules={})
  ad=AgentDefinition(tenant_id=t.id,slug=f"w8-def-{s}",name="W8 Customer Success Definition",capabilities=["execution"],allowed_tools=TOOLS,model_policy={},input_schema={},output_schema={},policy_requirements={},enabled=True);db.add_all([ev,ad]);await db.flush()
  pp={"permissions":["run.execute"],"allowed_tools":TOOLS}
  at=AgentTemplate(tenant_id=t.id,agent_definition_id=ad.id,slug=f"w8-template-{s}",name="W8 Customer Success Template",version=1,status=AgentTemplateStatus.PUBLISHED,risk_tier=0,capability_contract={"execution":True},permission_policy=pp,approval_policy={},evaluation_policy={"certification_fixture":True},install_policy={},published_at=datetime.now(timezone.utc));db.add(at);await db.flush()
  fp=execution_authority_fingerprint(tenant_id=t.id,template_id=at.id,template_version=1,agent_definition_id=ad.id,risk_tier=0,capability_contract=at.capability_contract,permission_policy=pp,approval_policy={},install_policy={},configuration={},max_concurrency=1,budget_policy={})
  ai=AgentInstance(tenant_id=t.id,agent_definition_id=ad.id,agent_template_id=at.id,sponsor_user_id=o.id,name="W8 Instance",configuration={FINGERPRINT_KEY:fp},permission_policy=pp,approval_policy={},risk_tier=0,max_concurrency=1,budget_policy={},enabled=True);db.add(ai);await db.flush()
  ident=AgentIdentity(tenant_id=t.id,agent_instance_id=ai.id,owner_user_id=o.id,sponsor_user_id=o.id,subject=f"agent:{t.id}:{ai.id}",active=True);db.add(ident);await db.flush()
  db.add(AgentAccessReview(tenant_id=t.id,agent_identity_id=ident.id,reviewer_user_id=rv.id,decision=AgentAccessReviewDecision.APPROVED,reason="Controlled W8 certification"))
  db.add(AgentRuntimeBinding(tenant_id=t.id,agent_definition_id=ad.id,employee_version_id=ev.id,is_active=True))
  rr=Run(tenant_id=t.id,employee_id=e.id,employee_version_id=ev.id,agent_instance_id=ai.id,created_by=o.id,status="pending",input_data={"purpose":"W8 research"})
  ar=Run(tenant_id=t.id,employee_id=e.id,employee_version_id=ev.id,agent_instance_id=ai.id,created_by=o.id,status="pending",input_data={"purpose":"W8 action"})
  db.add_all([rr,ar]);await db.flush()
  args={"customer_reference":"customer-001","message":"Support response prepared for review."}
  ap=ToolApprovalRequest(tenant_id=t.id,run_id=ar.id,tool_name="workforce_send_customer_message",tool_call_id=f"w8-{uuid.uuid4().hex}",arguments=args,continuation_messages=[],iteration=0,status="approved",requested_by=o.id,decided_by=rv.id,decision_reason="Controlled W8 certification",decided_at=datetime.now(timezone.utc));db.add(ap);await db.commit()
  return t.id,ai.id,rr.id,ar.id,ap.tool_call_id

async def execute(t,a,r,tool,args,call=None):
 async with AsyncSessionLocal() as db:
  async with agent_tool_governance.agent_tool_context(tenant_id=t,agent_instance_id=a,run_id=r):
   out=await registry.execute(tool,args,permissions={"run.execute"},db=db,tenant_id=t,agent_instance_id=a,tool_call_id=call)
  await db.commit();return out

async def main():
 t,a,rr,ar,call=await prepare()
 research=await execute(t,a,rr,"workforce_customer_context",{"customer_reference":"customer-001","query":"support history and account health"})
 assert research["provider_execution"]=="not_configured" and research["approval_required"] is False and research["external_side_effect"] is False
 assert research["storage_key"].startswith(f"{t}/")
 assert _read_json(str(t),research["storage_key"])["provenance"]["tenant_id"]==str(t)
 action=await execute(t,a,ar,"workforce_send_customer_message",{"customer_reference":"customer-001","message":"Support response prepared for review."},call)
 assert action["approval_required"] is True and action["approval_status"]=="pending" and action["status"]=="proposal"
 assert action["provider_execution"]=="not_configured" and action["external_side_effect"] is True
 try: _read_json(str(uuid.uuid4()),action["storage_key"])
 except Exception: pass
 else: raise AssertionError("W8 cross-tenant artifact read unexpectedly succeeded")
 print("W8 CUSTOMER SUCCESS GOVERNED RESEARCH RUN PASS")
 print(f"W8 CUSTOMER SUCCESS ARTIFACT PASS artifact_id={research['artifact_id']}")
 print("W8 CUSTOMER ACTION APPROVAL GOVERNANCE PASS")
 print(f"W8 CUSTOMER MESSAGE PROPOSAL PASS artifact_id={action['artifact_id']}")
 print("W8 PROVENANCE AND TENANT ISOLATION PASS")
 print("W8 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
 print("WORKFORCE W8 CUSTOMER SUCCESS REAL-STACK E2E PASS")

if __name__=="__main__":
 try: asyncio.run(main())
 except Exception as exc:
  print(f"WORKFORCE W8 CUSTOMER SUCCESS REAL-STACK E2E FAIL: {exc}",file=sys.stderr);raise SystemExit(1)

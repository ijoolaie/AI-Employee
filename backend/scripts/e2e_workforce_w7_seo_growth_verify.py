"""W7 SEO & Growth real-stack certification."""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import datetime, timezone
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.employee import Employee,EmployeeVersion
from app.models.run import Run
from app.models.agent_instance import AgentInstance
from app.models.agent_template import AgentTemplate,AgentTemplateStatus
from app.models.tool_approval import ToolApprovalRequest
from app.models.user import User
from app.models.tenant import Tenant
from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_access_review import AgentAccessReview,AgentAccessReviewDecision
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.services import agent_tool_governance,edition_service,license_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY,execution_authority_fingerprint
from app.ai.tool_registry import registry
from app.services.workforce_semantic_domains import _read_json
TOOLS=[f"workforce_{x}" for x in ("keyword_research","content_opportunity_analysis","on_page_recommendations","technical_seo_check","internal_link_recommendations","content_brief","search_performance_ingestion","growth_report","seo_experiment_proposal")]
async def prepare():
 s=f"{os.environ.get('GITHUB_RUN_ID','local')}-{uuid.uuid4().hex[:8]}"
 async with AsyncSessionLocal() as db:
  v=Tenant(name=f"W7 Vendor {s}",slug=f"w7-vendor-{s}",status="active",tenant_kind=edition_service.EDITION_VENDOR);db.add(v);await db.flush()
  r=Tenant(name=f"W7 Reseller {s}",slug=f"w7-reseller-{s}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=v.id);db.add(r);await db.flush()
  t=Tenant(name=f"W7 Customer {s}",slug=f"w7-customer-{s}",status="active",tenant_kind=edition_service.EDITION_CUSTOMER,parent_tenant_id=r.id);db.add(t);await db.flush()
  o=User(tenant_id=t.id,email=f"w7-owner-{s}@example.invalid",password_hash="certification-fixture",full_name="W7 Owner",is_active=True)
  rv=User(tenant_id=t.id,email=f"w7-reviewer-{s}@example.invalid",password_hash="certification-fixture",full_name="W7 Reviewer",is_active=True);db.add_all([o,rv]);await db.flush()
  await license_service.issue_license(db,issuer=r,tenant=t,feature_codes=["employee.run"]+[f"tool:{x}" for x in TOOLS],metadata={"certification_fixture":True,"purpose":"W7-seo-growth-e2e"})
  e=Employee(tenant_id=t.id,slug=f"w7-seo-{s}",name="W7 SEO Growth Employee",kind="custom",is_active=True);db.add(e);await db.flush()
  ev=EmployeeVersion(employee_id=e.id,version_number=1,is_current=True,input_schema={},output_schema={},prompt_template="W7 SEO Growth Certification",allowed_tools=TOOLS,rules={})
  ad=AgentDefinition(tenant_id=t.id,slug=f"w7-def-{s}",name="W7 SEO Growth Definition",capabilities=["execution"],allowed_tools=TOOLS,model_policy={},input_schema={},output_schema={},policy_requirements={},enabled=True);db.add_all([ev,ad]);await db.flush()
  pp={"permissions":["run.execute"],"allowed_tools":TOOLS}
  at=AgentTemplate(tenant_id=t.id,agent_definition_id=ad.id,slug=f"w7-template-{s}",name="W7 SEO Template",version=1,status=AgentTemplateStatus.PUBLISHED,risk_tier=0,capability_contract={"execution":True},permission_policy=pp,approval_policy={},evaluation_policy={"certification_fixture":True},install_policy={},published_at=datetime.now(timezone.utc));db.add(at);await db.flush()
  fp=execution_authority_fingerprint(tenant_id=t.id,template_id=at.id,template_version=1,agent_definition_id=ad.id,risk_tier=0,capability_contract=at.capability_contract,permission_policy=pp,approval_policy={},install_policy={},configuration={},max_concurrency=1,budget_policy={})
  ai=AgentInstance(tenant_id=t.id,agent_definition_id=ad.id,agent_template_id=at.id,sponsor_user_id=o.id,name="W7 Instance",configuration={FINGERPRINT_KEY:fp},permission_policy=pp,approval_policy={},risk_tier=0,max_concurrency=1,budget_policy={},enabled=True);db.add(ai);await db.flush()
  ident=AgentIdentity(tenant_id=t.id,agent_instance_id=ai.id,owner_user_id=o.id,sponsor_user_id=o.id,subject=f"agent:{t.id}:{ai.id}",active=True);db.add(ident);await db.flush()
  db.add(AgentAccessReview(tenant_id=t.id,agent_identity_id=ident.id,reviewer_user_id=rv.id,decision=AgentAccessReviewDecision.APPROVED,reason="Controlled W7 certification"))
  db.add(AgentRuntimeBinding(tenant_id=t.id,agent_definition_id=ad.id,employee_version_id=ev.id,is_active=True))
  rr=Run(tenant_id=t.id,employee_id=e.id,employee_version_id=ev.id,agent_instance_id=ai.id,created_by=o.id,status="pending",input_data={"purpose":"W7 research"});pr=Run(tenant_id=t.id,employee_id=e.id,employee_version_id=ev.id,agent_instance_id=ai.id,created_by=o.id,status="pending",input_data={"purpose":"W7 experiment proposal"});db.add_all([rr,pr]);await db.flush()
  ap=ToolApprovalRequest(tenant_id=t.id,run_id=pr.id,tool_name="workforce_seo_experiment_proposal",tool_call_id=f"w7-{uuid.uuid4().hex}",arguments={"topic":"organic growth"},continuation_messages=[],iteration=0,status="approved",requested_by=o.id,decided_by=rv.id,decision_reason="Controlled W7 certification",decided_at=datetime.now(timezone.utc));db.add(ap);await db.commit()
  return t.id,ai.id,rr.id,pr.id,ap.tool_call_id
async def execute(t,a,r,tool,args,call=None):
 async with AsyncSessionLocal() as db:
  async with agent_tool_governance.agent_tool_context(tenant_id=t,agent_instance_id=a,run_id=r):
   out=await registry.execute(tool,args,permissions={"run.execute"},db=db,tenant_id=t,agent_instance_id=a,tool_call_id=call)
  await db.commit();return out
async def main():
 t,a,rr,pr,call=await prepare()
 research=await execute(t,a,rr,"workforce_keyword_research",{"topic":"SaaS customer acquisition"})
 assert research["provider_execution"]=="not_configured" and research["approval_required"] is False
 assert research["external_side_effect"] is False
 assert research["storage_key"].startswith(f"{t}/")
 p=_read_json(str(t),research["storage_key"]);assert p["provenance"]["tenant_id"]==str(t)
 proposal=await execute(t,a,pr,"workforce_seo_experiment_proposal",{"topic":"SaaS customer acquisition","spec":{"hypothesis":"improve organic conversion"}},call)
 assert proposal["approval_required"] is True and proposal["approval_status"]=="pending"
 assert proposal["status"]=="proposal" and proposal["provider_execution"]=="not_configured" and proposal["external_side_effect"] is True
 try:_read_json(str(uuid.uuid4()),proposal["storage_key"])
 except Exception:pass
 else:raise AssertionError("W7 cross-tenant artifact read unexpectedly succeeded")
 print("W7 SEO GROWTH EMPLOYEE GOVERNED RESEARCH RUN PASS")
 print(f"W7 SEO ARTIFACT PASS artifact_id={research['artifact_id']}")
 print("W7 SEO EXPERIMENT APPROVAL GOVERNANCE PASS")
 print(f"W7 SEO EXPERIMENT PROPOSAL PASS artifact_id={proposal['artifact_id']}")
 print("W7 PROVENANCE AND TENANT ISOLATION PASS")
 print("W7 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
 print("WORKFORCE W7 SEO GROWTH REAL-STACK E2E PASS")
if __name__=="__main__":
 try:asyncio.run(main())
 except Exception as e:print(f"WORKFORCE W7 SEO GROWTH REAL-STACK E2E FAIL: {e}",file=sys.stderr);raise SystemExit(1)

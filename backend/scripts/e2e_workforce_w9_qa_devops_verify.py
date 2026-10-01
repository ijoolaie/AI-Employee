"""W9 QA & DevOps real-stack certification."""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import datetime, timezone
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)

from app.ai.tool_registry import registry
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
from app.services.workforce_semantic_domains import _read_json

TOOLS=[
    "workforce_qa_test_plan","workforce_regression_analysis","workforce_ci_health_check",
    "workforce_release_readiness","workforce_incident_diagnostics","workforce_rollback_readiness",
    "workforce_deployment_proposal","workforce_rollback_proposal","workforce_production_change_proposal",
]

async def prepare():
    s=f"{os.environ.get('GITHUB_RUN_ID','local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        v=Tenant(name=f"W9 Vendor {s}",slug=f"w9-vendor-{s}",status="active",tenant_kind=edition_service.EDITION_VENDOR); db.add(v); await db.flush()
        r=Tenant(name=f"W9 Reseller {s}",slug=f"w9-reseller-{s}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=v.id); db.add(r); await db.flush()
        t=Tenant(name=f"W9 Customer {s}",slug=f"w9-customer-{s}",status="active",tenant_kind=edition_service.EDITION_CUSTOMER,parent_tenant_id=r.id); db.add(t); await db.flush()
        owner=User(tenant_id=t.id,email=f"w9-owner-{s}@example.invalid",password_hash="certification-fixture",full_name="W9 Owner",is_active=True)
        reviewer=User(tenant_id=t.id,email=f"w9-reviewer-{s}@example.invalid",password_hash="certification-fixture",full_name="W9 Reviewer",is_active=True)
        db.add_all([owner,reviewer]); await db.flush()
        await license_service.issue_license(
            db,issuer=r,tenant=t,
            feature_codes=["employee.run"]+[f"tool:{x}" for x in TOOLS],
            metadata={"certification_fixture":True,"purpose":"W9-qa-devops-e2e"},
        )
        e=Employee(tenant_id=t.id,slug=f"w9-qa-devops-{s}",name="W9 QA DevOps Employee",kind="custom",is_active=True); db.add(e); await db.flush()
        ev=EmployeeVersion(employee_id=e.id,version_number=1,is_current=True,input_schema={},output_schema={},prompt_template="W9 QA DevOps Certification",allowed_tools=TOOLS,rules={})
        ad=AgentDefinition(tenant_id=t.id,slug=f"w9-def-{s}",name="W9 QA DevOps Definition",capabilities=["execution"],allowed_tools=TOOLS,model_policy={},input_schema={},output_schema={},policy_requirements={},enabled=True)
        db.add_all([ev,ad]); await db.flush()
        pp={"permissions":["run.execute"],"allowed_tools":TOOLS}
        at=AgentTemplate(tenant_id=t.id,agent_definition_id=ad.id,slug=f"w9-template-{s}",name="W9 QA DevOps Template",version=1,status=AgentTemplateStatus.PUBLISHED,risk_tier=0,capability_contract={"execution":True},permission_policy=pp,approval_policy={},evaluation_policy={"certification_fixture":True},install_policy={},published_at=datetime.now(timezone.utc))
        db.add(at); await db.flush()
        fp=execution_authority_fingerprint(tenant_id=t.id,template_id=at.id,template_version=1,agent_definition_id=ad.id,risk_tier=0,capability_contract=at.capability_contract,permission_policy=pp,approval_policy={},install_policy={},configuration={},max_concurrency=1,budget_policy={})
        ai=AgentInstance(tenant_id=t.id,agent_definition_id=ad.id,agent_template_id=at.id,sponsor_user_id=owner.id,name="W9 Instance",configuration={FINGERPRINT_KEY:fp},permission_policy=pp,approval_policy={},risk_tier=0,max_concurrency=1,budget_policy={},enabled=True)
        db.add(ai); await db.flush()
        ident=AgentIdentity(tenant_id=t.id,agent_instance_id=ai.id,owner_user_id=owner.id,sponsor_user_id=owner.id,subject=f"agent:{t.id}:{ai.id}",active=True); db.add(ident); await db.flush()
        db.add(AgentAccessReview(tenant_id=t.id,agent_identity_id=ident.id,reviewer_user_id=reviewer.id,decision=AgentAccessReviewDecision.APPROVED,reason="Controlled W9 certification"))
        db.add(AgentRuntimeBinding(tenant_id=t.id,agent_definition_id=ad.id,employee_version_id=ev.id,is_active=True))
        research=Run(tenant_id=t.id,employee_id=e.id,employee_version_id=ev.id,agent_instance_id=ai.id,created_by=owner.id,status="pending",input_data={"purpose":"W9 quality research"})
        action=Run(tenant_id=t.id,employee_id=e.id,employee_version_id=ev.id,agent_instance_id=ai.id,created_by=owner.id,status="pending",input_data={"purpose":"W9 deployment proposal"})
        db.add_all([research,action]); await db.flush()
        args={"repository":"certification-fixture","commit_sha":"0"*40,"test_scope":"release-gate","recommendation":"review deployment readiness before external execution"}
        approval=ToolApprovalRequest(
            tenant_id=t.id,run_id=action.id,tool_name="workforce_deployment_proposal",
            tool_call_id=f"w9-{uuid.uuid4().hex}",arguments=args,continuation_messages=[],iteration=0,
            status="approved",requested_by=owner.id,decided_by=reviewer.id,
            decision_reason="Controlled W9 certification",decided_at=datetime.now(timezone.utc),
        )
        db.add(approval); await db.commit()
        return t.id,ai.id,research.id,action.id,approval.tool_call_id,args

async def execute(tenant_id,agent_id,run_id,tool,args,call=None):
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id,agent_instance_id=agent_id,run_id=run_id):
            out=await registry.execute(tool,args,permissions={"run.execute"},db=db,tenant_id=tenant_id,agent_instance_id=agent_id,tool_call_id=call)
        await db.commit()
        return out

async def main():
    tenant_id,agent_id,research_run,action_run,call,args=await prepare()
    research_args={"repository":"certification-fixture","commit_sha":"0"*40,"test_scope":"full-regression"}
    research=await execute(tenant_id,agent_id,research_run,"workforce_qa_test_plan",research_args)
    assert research["provider_execution"]=="not_configured" and research["approval_required"] is False
    assert research["external_side_effect"] is False
    assert research["storage_key"].startswith(f"{tenant_id}/")
    assert _read_json(str(tenant_id),research["storage_key"])["provenance"]["tenant_id"]==str(tenant_id)

    proposal=await execute(tenant_id,agent_id,action_run,"workforce_deployment_proposal",args,call)
    assert proposal["approval_required"] is True and proposal["approval_status"]=="pending" and proposal["status"]=="proposal"
    assert proposal["provider_execution"]=="not_configured" and proposal["external_side_effect"] is True
    try: _read_json(str(uuid.uuid4()),proposal["storage_key"])
    except Exception: pass
    else: raise AssertionError("W9 cross-tenant artifact read unexpectedly succeeded")

    print("W9 QA DEVOPS GOVERNED RESEARCH RUN PASS")
    print(f"W9 QA ARTIFACT PASS artifact_id={research['artifact_id']}")
    print("W9 DEPLOYMENT APPROVAL GOVERNANCE PASS")
    print(f"W9 DEPLOYMENT PROPOSAL PASS artifact_id={proposal['artifact_id']}")
    print("W9 PROVENANCE AND TENANT ISOLATION PASS")
    print("W9 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("WORKFORCE W9 QA DEVOPS REAL-STACK E2E PASS")

if __name__=="__main__":
    try: asyncio.run(main())
    except Exception as exc:
        print(f"WORKFORCE W9 QA DEVOPS REAL-STACK E2E FAIL: {exc}",file=sys.stderr)
        raise SystemExit(1)

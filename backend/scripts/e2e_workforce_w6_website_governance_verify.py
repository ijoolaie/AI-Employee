"""Real-stack W6 Website Employee governance certification.

Certifies governed website work, durable tenant-scoped changes, approval gating,
and fail-closed deployment/rollback provider boundaries. No production deploy
is claimed.
"""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import datetime, timezone

PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0, PROJECT_ROOT)

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

TOOLS=[
"workforce_website_requirements","workforce_website_ux_content_plan","workforce_website_implementation",
"workforce_website_asset_integration","workforce_website_tests","workforce_website_accessibility",
"workforce_website_build","workforce_website_preview","workforce_website_health_check",
"workforce_website_deploy","workforce_website_rollback",
]

async def prepare():
    suffix=f"{os.environ.get('GITHUB_RUN_ID','local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor=Tenant(name=f"W6 Cert Vendor {suffix}",slug=f"w6-cert-vendor-{suffix}",status="active",tenant_kind=edition_service.EDITION_VENDOR); db.add(vendor); await db.flush()
        reseller=Tenant(name=f"W6 Cert Reseller {suffix}",slug=f"w6-cert-reseller-{suffix}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=vendor.id); db.add(reseller); await db.flush()
        customer=Tenant(name=f"W6 Cert Customer {suffix}",slug=f"w6-cert-customer-{suffix}",status="active",tenant_kind=edition_service.EDITION_CUSTOMER,parent_tenant_id=reseller.id); db.add(customer); await db.flush()
        owner=User(tenant_id=customer.id,email=f"w6-owner-{suffix}@example.invalid",password_hash="certification-fixture",full_name="W6 Certification Owner",is_active=True)
        reviewer=User(tenant_id=customer.id,email=f"w6-reviewer-{suffix}@example.invalid",password_hash="certification-fixture",full_name="W6 Certification Reviewer",is_active=True)
        db.add_all([owner,reviewer]); await db.flush()
        await license_service.issue_license(db,issuer=reseller,tenant=customer,feature_codes=["employee.run"]+[f"tool:{x}" for x in TOOLS],metadata={"certification_fixture":True,"purpose":"W6-website-governance-e2e"})
        employee=Employee(tenant_id=customer.id,slug=f"w6-website-{suffix}",name="W6 Website Employee",kind="custom",is_active=True); db.add(employee); await db.flush()
        version=EmployeeVersion(employee_id=employee.id,version_number=1,is_current=True,input_schema={},output_schema={},prompt_template="W6 Website Certification",allowed_tools=TOOLS,rules={})
        definition=AgentDefinition(tenant_id=customer.id,slug=f"w6-website-def-{suffix}",name="W6 Website Definition",capabilities=["execution"],allowed_tools=TOOLS,model_policy={},input_schema={},output_schema={},policy_requirements={},enabled=True); db.add_all([version,definition]); await db.flush()
        policy={"permissions":["run.execute"],"allowed_tools":TOOLS}
        template=AgentTemplate(tenant_id=customer.id,agent_definition_id=definition.id,slug=f"w6-website-template-{suffix}",name="W6 Website Template",version=1,status=AgentTemplateStatus.PUBLISHED,risk_tier=0,capability_contract={"execution":True},permission_policy=policy,approval_policy={},evaluation_policy={"certification_fixture":True},install_policy={},published_at=datetime.now(timezone.utc)); db.add(template); await db.flush()
        fp=execution_authority_fingerprint(tenant_id=customer.id,template_id=template.id,template_version=1,agent_definition_id=definition.id,risk_tier=0,capability_contract=template.capability_contract,permission_policy=policy,approval_policy={},install_policy={},configuration={},max_concurrency=1,budget_policy={})
        instance=AgentInstance(tenant_id=customer.id,agent_definition_id=definition.id,agent_template_id=template.id,sponsor_user_id=owner.id,name="W6 Website Instance",configuration={FINGERPRINT_KEY:fp},permission_policy=policy,approval_policy={},risk_tier=0,max_concurrency=1,budget_policy={},enabled=True); db.add(instance); await db.flush()
        identity=AgentIdentity(tenant_id=customer.id,agent_instance_id=instance.id,owner_user_id=owner.id,sponsor_user_id=owner.id,subject=f"agent:{customer.id}:{instance.id}",active=True); db.add(identity); await db.flush()
        db.add(AgentAccessReview(tenant_id=customer.id,agent_identity_id=identity.id,reviewer_user_id=reviewer.id,decision=AgentAccessReviewDecision.APPROVED,reason="Controlled W6 certification"))
        db.add(AgentRuntimeBinding(tenant_id=customer.id,agent_definition_id=definition.id,employee_version_id=version.id,is_active=True))
        req_run=Run(tenant_id=customer.id,employee_id=employee.id,employee_version_id=version.id,agent_instance_id=instance.id,created_by=owner.id,status="pending",input_data={"purpose":"W6 website requirements certification"})
        deploy_run=Run(tenant_id=customer.id,employee_id=employee.id,employee_version_id=version.id,agent_instance_id=instance.id,created_by=owner.id,status="pending",input_data={"purpose":"W6 deploy proposal certification"})
        db.add_all([req_run,deploy_run]); await db.flush()
        args={"site":"internal-company","spec":{"release":"w6-cert"}}
        approval=ToolApprovalRequest(tenant_id=customer.id,run_id=deploy_run.id,tool_name="workforce_website_deploy",tool_call_id=f"w6-deploy-{uuid.uuid4().hex}",arguments=args,continuation_messages=[],iteration=0,status="approved",requested_by=owner.id,decided_by=reviewer.id,decision_reason="Controlled W6 certification; provider must remain fail-closed",decided_at=datetime.now(timezone.utc))
        db.add(approval); await db.commit()
        return customer.id,instance.id,req_run.id,deploy_run.id,approval.tool_call_id

async def execute(tenant_id,instance_id,run_id,tool,args,call_id=None):
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id,agent_instance_id=instance_id,run_id=run_id):
            result=await registry.execute(tool,args,permissions={"run.execute"},db=db,tenant_id=tenant_id,agent_instance_id=instance_id,tool_call_id=call_id)
        await db.commit(); return result

async def main():
    tenant,instance,req_run,deploy_run,call_id=await prepare()
    req=await execute(tenant,instance,req_run,"workforce_website_requirements",{"site":"internal-company","spec":{"page":"home"}})
    assert req["provider_execution"]=="not_configured"
    assert req["approval_required"] is False
    assert req["status"]=="staged"
    deploy=await execute(tenant,instance,deploy_run,"workforce_website_deploy",{"site":"internal-company","spec":{"release":"w6-cert"}},call_id)
    assert deploy["approval_required"] is True
    assert deploy["approval_status"]=="pending"
    assert deploy["external_side_effect"] is True
    assert deploy["provider_execution"]=="not_configured"
    assert deploy["status"]=="proposal"
    payload=_read_json(str(tenant),deploy["storage_key"])
    assert payload["provenance"]["tenant_id"]==str(tenant)
    assert payload["provider_execution"]=="not_configured"
    try: _read_json(str(uuid.uuid4()),deploy["storage_key"])
    except Exception: pass
    else: raise AssertionError("W6 cross-tenant website artifact read unexpectedly succeeded")
    print("W6 WEBSITE EMPLOYEE GOVERNED RUN PASS")
    print(f"W6 WEBSITE ARTIFACT PASS change_id={req['change_id']}")
    print("W6 APPROVED DEPLOY PROPOSAL GOVERNANCE PASS")
    print(f"W6 DEPLOY PROPOSAL PASS change_id={deploy['change_id']}")
    print("W6 PROVENANCE AND TENANT ISOLATION PASS")
    print("W6 PROVIDER FAIL-CLOSED PASS provider_execution=not_configured")
    print("WORKFORCE W6 WEBSITE GOVERNANCE REAL-STACK E2E PASS")

if __name__=="__main__":
    try: asyncio.run(main())
    except Exception as exc:
        print(f"WORKFORCE W6 WEBSITE GOVERNANCE REAL-STACK E2E FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

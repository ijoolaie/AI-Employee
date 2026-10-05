"""Real-stack W20 third-party Employee Marketplace evidence E2E."""
from __future__ import annotations
import asyncio,json,os,sys,time,uuid
from urllib.request import Request,urlopen
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
from app.core.database import AsyncSessionLocal
from app.models.agent_definition import AgentDefinition
from app.models.agent_evaluation import AgentEvaluation,AgentEvaluationStatus
from app.models.agent_template import AgentTemplate,AgentTemplateStatus
from app.models.employee_marketplace import EmployeeMarketplaceInstallationStatus
BASE_URL=os.environ.get("E2E_API_BASE_URL","http://localhost:8000/api/v1")

def request(method,path,token,payload=None,expected=200):
    body=None if payload is None else json.dumps(payload).encode()
    with urlopen(Request(BASE_URL+path,data=body,headers={"Accept":"application/json","Content-Type":"application/json","Authorization":f"Bearer {token}"},method=method),timeout=20) as r:
        data=json.loads(r.read().decode()); assert r.status==expected,data; return data

def register(suffix):
    payload={"tenant_name":f"W20 Employee E2E {suffix}","tenant_slug":f"w20-employee-{suffix}","email":f"w20-owner-{suffix}@example.com","password":"W20EmployeeE2E-2026!","full_name":"W20 CEO"}
    d=request("POST","/auth/register",None,payload,201); token=d["data"]["access_token"]
    me=request("GET","/auth/me",token)
    return uuid.UUID(me["data"]["tenant"]["id"]),uuid.UUID(me["data"]["user"]["id"]),token

async def seed_seller(tenant_id,owner_id,suffix):
    async with AsyncSessionLocal() as db:
        definition=AgentDefinition(
            tenant_id=tenant_id,slug=f"w20-source-{suffix}",name="W20 Specialist",
            description="W20 fixture",version=1,capabilities=["research"],allowed_tools=[],
            model_policy={"provider":"operator-controlled"},input_schema={},output_schema={},
            policy_requirements={},enabled=True)
        db.add(definition); await db.flush()
        template=AgentTemplate(
            tenant_id=tenant_id,agent_definition_id=definition.id,slug=f"w20-template-{suffix}",
            name="W20 Specialist Template",description="W20 fixture",version=1,
            status=AgentTemplateStatus.PUBLISHED,risk_tier=2,capability_contract={"workforce_role_code":"ai_internal_manager"},
            permission_policy={"permissions":["run.execute"]},approval_policy={"requires_ceo_approval":True},
            evaluation_policy={"required_contract_version":"agent-evaluation-v1"},install_policy={"requires_ceo_approval":True},
            is_system_template=False)
        db.add(template); await db.flush()
        evaluation=AgentEvaluation(
            tenant_id=tenant_id,agent_template_id=template.id,suite_id="w20-fixture-suite",
            status=AgentEvaluationStatus.PASSED,score=100,
            evidence={"contract_version":"agent-evaluation-v1","fixture":True},
            evaluator_user_id=owner_id,notes="W20 real-stack fixture")
        import hashlib
        evaluation.evidence_hash=hashlib.sha256(json.dumps(evaluation.evidence,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        db.add(evaluation); await db.commit()
        return template.id

def expect403_or404(token,path):
    try:
        request("POST",path,token,{"sponsor_user_id":str(uuid.uuid4())},200)
    except Exception as exc:
        code=getattr(exc,"code",None)
        if code not in (403,404): raise

async def run():
    suffix=str(time.time_ns())[-10:]
    seller_tenant,seller_owner,seller_token=register(suffix+"-seller")
    buyer_tenant,buyer_owner,buyer_token=register(suffix+"-buyer")
    template_id=await seed_seller(seller_tenant,seller_owner,suffix)
    package=request("POST","/employee-marketplace/packages",seller_token,{
        "source_agent_template_id":str(template_id),"slug":"w20-specialist","name":"W20 Specialist",
        "version":1,"description":"Governed third-party employee package","visibility":"public",
        "skill_package_ids":[],"workflow_refs":[],"visual_pack":{"theme":"technical"}} ,201)["data"]
    assert package["status"]=="published"
    assert package["permission_manifest"]["execution_authority_granted"] is False
    package_id=package["id"]
    try:
        request("POST",f"/employee-marketplace/packages/{package_id}/install",seller_token,{"sponsor_user_id":str(seller_owner)},200)
        raise AssertionError("seller tenant unexpectedly installed its own package")
    except Exception as exc:
        if getattr(exc,"code",None) not in (400,409): raise
    installation=request("POST",f"/employee-marketplace/packages/{package_id}/install",buyer_token,{"sponsor_user_id":str(buyer_owner)},201)["data"]
    assert installation["status"]=="active"
    assert installation["provider_execution_status"]=="NOT_VERIFIED"
    revoke=request("POST",f"/employee-marketplace/installations/{installation['id']}/revoke",buyer_token,None,200)["data"]
    assert revoke["status"]=="revoked"
    print("W20 PACKAGE PUBLICATION PASS")
    print("W20 CROSS-TENANT INSTALLATION PASS")
    print("W20 EXECUTION AUTHORITY FAIL-CLOSED PASS")
    print("W20 PROVIDER EXECUTION NOT-VERIFIED PASS")
    print("W20 REVOCATION PASS")
    print("WORKFORCE W20 EMPLOYEE-MARKETPLACE REAL-STACK E2E PASS")

if __name__=="__main__":
    try: asyncio.run(run())
    except Exception as exc:
        print(f"WORKFORCE W20 EMPLOYEE-MARKETPLACE REAL-STACK E2E FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

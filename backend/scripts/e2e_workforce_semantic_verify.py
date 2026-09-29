"""Real-stack semantic Workforce E2E certification."""
from __future__ import annotations
import asyncio, json, os, sys, time, uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.agent_access_review import AgentAccessReviewDecision
from app.models.agent_definition import AgentDefinition
from app.models.agent_evaluation import AgentEvaluationStatus
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.audit_log import AuditLog
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.user import User
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services import edition_service, license_service
from app.services.agent_governance import record_evaluation, review_access
from app.services.agent_template_service import create_template, publish_template
from app.services.agent_workforce_proposal_service import create_proposal, board_decide, ceo_decide, provision_approved_proposal, activate_provisioned_proposal
from app.services.ai_workforce_roles import workforce_capability_contract_snapshot, workforce_template_capability_contract
from app.services.workforce_runtime_governance import assert_workforce_operation

BASE_URL=os.environ.get("E2E_API_BASE_URL","http://localhost:8000/api/v1")

def req(method,path,payload=None,token=None):
    body=None if payload is None else json.dumps(payload).encode()
    h={"Accept":"application/json","Content-Type":"application/json"}
    if token: h["Authorization"]=f"Bearer {token}"
    try:
        with urlopen(Request(f"{BASE_URL}{path}",data=body,headers=h,method=method),timeout=20) as r:
            raw=r.read().decode(); return r.status,json.loads(raw) if raw else None
    except HTTPError as e:
        raw=e.read().decode()
        try: detail=json.loads(raw)
        except json.JSONDecodeError: detail={"raw":raw}
        raise AssertionError(f"{method} {path} HTTP {e.code}: {detail}") from e
    except URLError as e: raise AssertionError(f"{method} {path} unavailable: {e}") from e

async def new_user(db,tenant_id,suffix,label):
    u=User(tenant_id=tenant_id,email=f"e2e-{label}-{suffix}@example.invalid",password_hash="fixture",full_name=f"E2E {label}",is_active=True)
    db.add(u); await db.flush(); return u

async def license_fixture(tenant_id,suffix):
    async with AsyncSessionLocal() as db:
        t=(await db.execute(select(Tenant).where(Tenant.id==tenant_id))).scalar_one()
        t.tenant_kind=edition_service.EDITION_CUSTOMER
        vendor=Tenant(name=f"E2E Vendor {suffix}",slug=f"e2e-vendor-{suffix}",status="active",tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor); await db.flush()
        reseller=Tenant(name=f"E2E Reseller {suffix}",slug=f"e2e-reseller-{suffix}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=vendor.id)
        db.add(reseller); await db.flush(); t.parent_tenant_id=reseller.id
        row=await license_service.issue_license(db,issuer=reseller,tenant=t,feature_codes=["employee.run","tool:workforce_market_research"],metadata={"certification_fixture":True,"purpose":"workforce-semantic-e2e"})
        assert row.status=="active"; await db.commit()

async def governed_agent(tenant_id,suffix,owner_id,variant):
    async with AsyncSessionLocal() as db:
        sponsor=await new_user(db,tenant_id,suffix,f"sponsor-{variant}")
        board=await new_user(db,tenant_id,suffix,f"board-{variant}")
        ceo=await new_user(db,tenant_id,suffix,f"ceo-{variant}")
        activator=await new_user(db,tenant_id,suffix,f"activator-{variant}")
        employee=Employee(tenant_id=tenant_id,slug=f"e2e-trader-{suffix}-{variant}",name=f"E2E Trader {variant}",kind="custom",is_active=True)
        db.add(employee); await db.flush()
        output={"type":"object","properties":{"content":{"type":"string"}},"required":["content"]}
        version=EmployeeVersion(employee_id=employee.id,version_number=1,is_current=True,input_schema={},output_schema=output,prompt_template="Perform deterministic market research.",allowed_tools=["workforce_market_research"],rules={})
        definition=AgentDefinition(tenant_id=tenant_id,slug=f"e2e-trader-def-{suffix}-{variant}",name=f"E2E Trader {variant}",capabilities=["execution"],allowed_tools=["workforce_market_research"],model_policy={},input_schema={},output_schema=output,policy_requirements={},enabled=True)
        db.add_all([version,definition]); await db.flush()
        template=await create_template(db,tenant_id=tenant_id,agent_definition_id=definition.id,slug=f"e2e-trader-template-{suffix}-{variant}",name=f"E2E Trader Template {variant}",version=1,risk_tier=0,capability_contract=workforce_template_capability_contract("ai_trader"),permission_policy={"permissions":["run.execute"],"allowed_tools":["workforce_market_research"]},approval_policy={},evaluation_policy={},install_policy={"requires_ceo_approval":True})
        await record_evaluation(db,tenant_id=tenant_id,template_id=template.id,suite_id="workforce-semantic-e2e-v1",status=AgentEvaluationStatus.PASSED,evidence={"contract_version":"v1","fixture":True},score=100,evaluator_user_id=board.id,notes="E2E fixture")
        await publish_template(db,tenant_id=tenant_id,template_id=template.id,approved_by_user_id=ceo.id)
        config={"workforce_role_code":"ai_trader","workforce_capability_contract":workforce_capability_contract_snapshot("ai_trader"),"max_concurrency":1,"budget_policy":{},"e2e_variant":variant}
        proposal=await create_proposal(db,tenant_id=tenant_id,requester_user_id=owner_id,title=f"E2E Trader {variant}",rationale="Semantic runtime certification",requested_name=f"E2E Trader {variant}",sponsor_user_id=sponsor.id,agent_template_id=template.id,risk_tier=0,configuration=config)
        await board_decide(db,tenant_id=tenant_id,proposal_id=proposal.id,reviewer_user_id=board.id,approve=True,reason="E2E")
        await ceo_decide(db,tenant_id=tenant_id,proposal_id=proposal.id,approver_user_id=ceo.id,approve=True,reason="E2E")
        await provision_approved_proposal(db,tenant_id=tenant_id,proposal_id=proposal.id)
        instance_id=proposal.provisioned_agent_instance_id
        identity=(await db.execute(select(AgentIdentity).where(AgentIdentity.agent_instance_id==instance_id,AgentIdentity.tenant_id==tenant_id))).scalar_one()
        await review_access(db,tenant_id=tenant_id,identity_id=identity.id,reviewer_user_id=activator.id,decision=AgentAccessReviewDecision.APPROVED,next_review_at=None,reason="E2E")
        await activate_provisioned_proposal(db,tenant_id=tenant_id,proposal_id=proposal.id,activated_by_user_id=activator.id)
        db.add(AgentRuntimeBinding(tenant_id=tenant_id,agent_definition_id=definition.id,employee_version_id=version.id,is_active=True))
        await db.commit()
        return instance_id,version.id,definition.id

async def work_item(tenant_id,agent_id,suffix,variant):
    async with AsyncSessionLocal() as db:
        w=WorkItem(tenant_id=tenant_id,title=f"Semantic Workforce {variant}",status=WorkItemStatus.READY,executor_type=ExecutorType.AGENT,executor_id=agent_id,input_data={"request":"market research"},policy_context={},idempotency_key=f"semantic-{suffix}-{variant}")
        db.add(w); await db.commit(); return w.id

async def wait_result(wid):
    for _ in range(100):
        async with AsyncSessionLocal() as db:
            w=await db.get(WorkItem,wid)
            if w and w.status in {WorkItemStatus.SUCCESS,WorkItemStatus.FAILED}:
                rid=(w.output_data or {}).get("run_id")
                run=await db.get(Run,uuid.UUID(rid)) if rid else None
                return w,run
        await asyncio.sleep(.25)
    raise AssertionError("WorkItem execution timed out")

async def verify_audit(tenant_id,run_id):
    async with AsyncSessionLocal() as db:
        rows=(await db.execute(select(AuditLog).where(AuditLog.tenant_id==tenant_id,AuditLog.resource_type=="run",AuditLog.resource_id==str(run_id),AuditLog.action=="tool.call"))).scalars().all()
        assert rows
        meta=rows[-1].metadata_ or {}
        assert rows[-1].status=="success" and meta.get("tool")=="workforce_market_research"
        assert meta.get("tool_call_id")=="e2e-workforce-market-research-1"

async def run_matrix(token,tenant_id,owner_id,suffix):
    await license_fixture(tenant_id,suffix)
    good,version,definition_id=await governed_agent(tenant_id,suffix,owner_id,"allowed")
    wid=await work_item(tenant_id,good,suffix,"allowed")
    assert req("POST",f"/work-items/{wid}/assign/agent",{"agent_instance_id":str(good)},token)[0]==200
    assert req("POST",f"/work-items/{wid}/dispatch",token=token)[0]==200
    w,run=await wait_result(wid)
    assert w.status is WorkItemStatus.SUCCEEDED and run and run.status=="success"
    await verify_audit(tenant_id,run.id)
    assert run.agent_instance_id == good
    assert run.employee_version_id == version
    async with AsyncSessionLocal() as db:
        binding=(await db.execute(select(AgentRuntimeBinding).where(
            AgentRuntimeBinding.tenant_id==tenant_id,
            AgentRuntimeBinding.agent_definition_id==definition_id,
            AgentRuntimeBinding.employee_version_id==version,
            AgentRuntimeBinding.is_active.is_(True),
        ))).scalar_one_or_none()
        assert binding is not None
    print("WORKFORCE SEMANTIC RUNTIME-BINDING CORRELATION REAL-STACK PASS")
    print("WORKFORCE SEMANTIC ALLOWED TOOL REAL-STACK PASS")

    wrong,_,_=await governed_agent(tenant_id,suffix,owner_id,"wrong-role")
    async with AsyncSessionLocal() as db:
        a=(await db.execute(select(AgentInstance).where(AgentInstance.id==wrong,AgentInstance.tenant_id==tenant_id))).scalar_one()
        a.configuration={**a.configuration,"workforce_role_code":"ai_marketing_advertising_manager"}; await db.commit()
    wid=await work_item(tenant_id,wrong,suffix,"wrong-role")
    assert req("POST",f"/work-items/{wid}/assign/agent",{"agent_instance_id":str(wrong)},token)[0]==200
    assert req("POST",f"/work-items/{wid}/dispatch",token=token)[0]==200
    w,run=await wait_result(wid)
    assert w.status is WorkItemStatus.FAILED and run and "not bound to the executing Agent role" in (run.error_message or "")
    print("WORKFORCE SEMANTIC WRONG-ROLE DENIAL REAL-STACK PASS")

    stale,stale_version,_=await governed_agent(tenant_id,suffix,owner_id,"stale-capability")
    async with AsyncSessionLocal() as db:
        agent=(await db.execute(select(AgentInstance).where(AgentInstance.id==stale,AgentInstance.tenant_id==tenant_id))).scalar_one()
        agent.configuration={**agent.configuration,"workforce_capability_contract":[{"operation":"tampered","tool_names":["workforce_market_research"]}]}
        await db.commit()
    wid=await work_item(tenant_id,stale,suffix,"stale-capability")
    assert req("POST",f"/work-items/{wid}/assign/agent",{"agent_instance_id":str(stale)},token)[0]==200
    assert req("POST",f"/work-items/{wid}/dispatch",token=token)[0]==200
    w,run=await wait_result(wid)
    assert w.status is WorkItemStatus.FAILED and run and "capability" in (run.error_message or "").lower()
    print("WORKFORCE SEMANTIC STALE-CAPABILITY DENIAL REAL-STACK PASS")

    async with AsyncSessionLocal() as db:
        agent=(await db.execute(select(AgentInstance).where(AgentInstance.id==good,AgentInstance.tenant_id==tenant_id))).scalar_one()
        try: await assert_workforce_operation(db,agent=agent,operation="order_execution")
        except Exception as exc:
            assert "approval" in str(exc).lower()
        else: raise AssertionError("approval-required operation was not denied")
    print("WORKFORCE SEMANTIC APPROVAL-REQUIRED DENIAL GOVERNANCE PASS")

def main():
    suffix=str(time.time_ns())[-10:]
    status,data=req("POST","/auth/register",{"tenant_name":f"Workforce Semantic E2E {suffix}","tenant_slug":f"workforce-semantic-{suffix}","email":f"workforce-semantic-{suffix}@example.invalid","password":"WorkforceSemanticE2E-2026!","full_name":"Workforce Semantic E2E Owner"})
    assert status==201,data
    token=data["data"]["access_token"]
    status,me=req("GET","/auth/me",token=token); assert status==200,me
    tenant_id=uuid.UUID(str(me["data"]["tenant"]["id"])); owner_id=uuid.UUID(str(me["data"]["user"]["id"]))
    asyncio.run(run_matrix(token,tenant_id,owner_id,suffix))
    print("WORKFORCE SEMANTIC REAL-STACK E2E MATRIX PASS")

if __name__=="__main__":
    try: main()
    except AssertionError as exc: print(f"WORKFORCE SEMANTIC REAL-STACK E2E MATRIX FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

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
from app.services import workforce_semantic_domains
from app.services.storage import get_storage_backend

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
    u=User(tenant_id=tenant_id,email=f"e2e-{label}-{suffix}@example.com",password_hash="fixture",full_name=f"E2E {label}",is_active=True)
    db.add(u); await db.flush(); return u

async def license_fixture(tenant_id,suffix):
    async with AsyncSessionLocal() as db:
        t=(await db.execute(select(Tenant).where(Tenant.id==tenant_id))).scalar_one()
        t.tenant_kind=edition_service.EDITION_CUSTOMER
        vendor=Tenant(name=f"E2E Vendor {suffix}",slug=f"e2e-vendor-{suffix}",status="active",tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor); await db.flush()
        reseller=Tenant(name=f"E2E Reseller {suffix}",slug=f"e2e-reseller-{suffix}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=vendor.id)
        db.add(reseller); await db.flush(); t.parent_tenant_id=reseller.id
        row=await license_service.issue_license(db,issuer=reseller,tenant=t,feature_codes=["employee.run","tool:workforce_market_research","tool:workforce_produce_article","tool:workforce_produce_social_caption","tool:workforce_create_visual_asset","tool:workforce_revise_visual_asset","tool:workforce_content_qa"],metadata={"certification_fixture":True,"purpose":"workforce-semantic-e2e"})
        assert row.status=="active"; await db.commit()

async def governed_agent(tenant_id,suffix,owner_id,variant,role_code="ai_trader",tool_name="workforce_market_research"):
    async with AsyncSessionLocal() as db:
        sponsor=await new_user(db,tenant_id,suffix,f"sponsor-{variant}")
        board=await new_user(db,tenant_id,suffix,f"board-{variant}")
        ceo=await new_user(db,tenant_id,suffix,f"ceo-{variant}")
        activator=await new_user(db,tenant_id,suffix,f"activator-{variant}")
        employee=Employee(tenant_id=tenant_id,slug=f"e2e-workforce-{suffix}-{variant}",name=f"E2E Workforce {variant}",kind="custom",is_active=True)
        db.add(employee); await db.flush()
        output={"type":"object","properties":{"content":{"type":"string"}},"required":["content"]}
        version=EmployeeVersion(employee_id=employee.id,version_number=1,is_current=True,input_schema={},output_schema=output,prompt_template=("Produce a draft article." if tool_name=="workforce_produce_article" else ("Prepare a social caption." if tool_name=="workforce_produce_social_caption" else ("Prepare a visual asset request." if tool_name=="workforce_create_visual_asset" else ("Revise a visual asset request." if tool_name=="workforce_revise_visual_asset" else ("Run deterministic content QA on the supplied title and body." if tool_name=="workforce_content_qa" else "Perform deterministic market research."))))),allowed_tools=[tool_name],rules={})
        definition=AgentDefinition(tenant_id=tenant_id,slug=f"e2e-workforce-def-{suffix}-{variant}",name=f"E2E Workforce {variant}",capabilities=["execution"],allowed_tools=[tool_name],model_policy={},input_schema={},output_schema=output,policy_requirements={},enabled=True)
        db.add_all([version,definition]); await db.flush()
        template=await create_template(db,tenant_id=tenant_id,agent_definition_id=definition.id,slug=f"e2e-workforce-template-{suffix}-{variant}",name=f"E2E Workforce Template {variant}",version=1,risk_tier=0,capability_contract=workforce_template_capability_contract(role_code),permission_policy={"permissions":["run.execute"],"allowed_tools":[tool_name]},approval_policy={},evaluation_policy={},install_policy={"requires_ceo_approval":True})
        await record_evaluation(db,tenant_id=tenant_id,template_id=template.id,suite_id="workforce-semantic-e2e-v1",status=AgentEvaluationStatus.PASSED,evidence={"contract_version":"v1","fixture":True},score=100,evaluator_user_id=board.id,notes="E2E fixture")
        await publish_template(db,tenant_id=tenant_id,template_id=template.id,approved_by_user_id=ceo.id)
        config={"workforce_role_code":role_code,"workforce_capability_contract":workforce_capability_contract_snapshot(role_code),"max_concurrency":1,"budget_policy":{},"e2e_variant":variant}
        proposal=await create_proposal(db,tenant_id=tenant_id,requester_user_id=owner_id,title=f"E2E Workforce {variant}",rationale="Semantic runtime certification",requested_name=f"E2E Workforce {variant}",sponsor_user_id=sponsor.id,agent_template_id=template.id,risk_tier=0,configuration=config)
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

async def work_item(tenant_id,agent_id,suffix,variant,request_text="market research"):
    async with AsyncSessionLocal() as db:
        w=WorkItem(tenant_id=tenant_id,title=f"Semantic Workforce {variant}",status=WorkItemStatus.READY,executor_type=ExecutorType.AGENT,executor_id=agent_id,input_data={"request":request_text},policy_context={},idempotency_key=f"semantic-{suffix}-{variant}")
        db.add(w); await db.commit(); return w.id

async def wait_result(wid):
    for _ in range(100):
        async with AsyncSessionLocal() as db:
            w=await db.get(WorkItem,wid)
            if w and w.status in {WorkItemStatus.SUCCEEDED,WorkItemStatus.FAILED}:
                rid=(w.output_data or {}).get("run_id")
                run=await db.get(Run,uuid.UUID(rid)) if rid else None
                return w,run
        await asyncio.sleep(.25)
    raise AssertionError("WorkItem execution timed out")

async def verify_audit(tenant_id,run_id,tool_name="workforce_market_research",tool_call_id="e2e-workforce-market-research-1"):
    async with AsyncSessionLocal() as db:
        rows=(await db.execute(select(AuditLog).where(AuditLog.tenant_id==tenant_id,AuditLog.resource_type=="run",AuditLog.resource_id==str(run_id),AuditLog.action=="tool.call"))).scalars().all()
        assert rows
        meta=rows[-1].metadata_ or {}
        assert rows[-1].status=="success" and meta.get("tool")==tool_name
        assert meta.get("tool_call_id")==tool_call_id

async def verify_cross_tenant_assignment(token, tenant_id, source_agent_id, suffix):
    other_suffix=f"{suffix}-cross"
    status, data=req("POST","/auth/register",{
        "tenant_name":f"Workforce Semantic E2E Cross Tenant {other_suffix}",
        "tenant_slug":f"workforce-semantic-cross-{other_suffix}",
        "email":f"workforce-semantic-cross-{other_suffix}@example.com",
        "password":"WorkforceSemanticE2E-2026!",
        "full_name":"Workforce Semantic E2E Cross Tenant",
    })
    assert status==201,data
    other_token=data["data"]["access_token"]
    status,me=req("GET","/auth/me",token=other_token); assert status==200,me
    other_tenant_id=uuid.UUID(str(me["data"]["tenant"]["id"]))
    wid=await work_item(other_tenant_id,source_agent_id,suffix,"cross-tenant")
    try:
        req("POST",f"/work-items/{wid}/assign/agent",{"agent_instance_id":str(source_agent_id)},other_token)
    except AssertionError as exc:
        assert "HTTP 404" in str(exc) or "HTTP 409" in str(exc), str(exc)
        print("WORKFORCE SEMANTIC CROSS-TENANT DENIAL REAL-STACK PASS")
        return
    raise AssertionError("cross-tenant Agent assignment unexpectedly succeeded")

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

    # Exercise the Content Producer through the same public WorkItem lifecycle:
    # assign -> dispatch -> Celery worker -> canonical Run -> governed tool call.
    content_agent,content_version,content_definition_id=await governed_agent(
        tenant_id,suffix,owner_id,"content-producer",role_code="ai_content_producer",tool_name="workforce_produce_article")
    content_title="Semantic E2E governed article"
    content_item=await work_item(tenant_id,content_agent,suffix,"content-producer",request_text=f"Produce an article titled {content_title}")
    assert req("POST",f"/work-items/{content_item}/assign/agent",{"agent_instance_id":str(content_agent)},token)[0]==200
    assert req("POST",f"/work-items/{content_item}/dispatch",token=token)[0]==200
    content_work,content_run=await wait_result(content_item)
    assert content_work.status is WorkItemStatus.SUCCEEDED and content_run and content_run.status=="success", (content_work.status,content_run.error_message if content_run else None)
    assert content_run.agent_instance_id==content_agent and content_run.employee_version_id==content_version
    await verify_audit(tenant_id,content_run.id,tool_name="workforce_produce_article",tool_call_id="e2e-workforce-produce-article-1")
    keys=get_storage_backend().list_prefix(f"{tenant_id}/")
    article_payloads=[]
    for key in keys:
        if "content-" in key and key.endswith(".json"):
            payload=workforce_semantic_domains._read_json(str(tenant_id),key)
            if payload.get("title")==content_title:
                article_payloads.append((key,payload))
    assert len(article_payloads)==1, f"expected one persisted content artifact for {content_title}, got {len(article_payloads)}"
    artifact_key,artifact=article_payloads[0]
    assert artifact["kind"]=="content_artifact" and artifact["status"]=="draft"
    assert artifact["provenance"]["tenant_id"]==str(tenant_id)
    assert artifact["provenance"]["provider_execution"]=="not_required"
    assert artifact["approval_status"]=="not_required"
    async with AsyncSessionLocal() as db:
        content_binding=(await db.execute(select(AgentRuntimeBinding).where(
            AgentRuntimeBinding.tenant_id==tenant_id,
            AgentRuntimeBinding.agent_definition_id==content_definition_id,
            AgentRuntimeBinding.employee_version_id==content_version,
            AgentRuntimeBinding.is_active.is_(True),
        ))).scalar_one_or_none()
        assert content_binding is not None
    print("WORKFORCE CONTENT PRODUCER WORKITEM -> DISPATCH -> WORKER -> RUN PASS")
    print(f"WORKFORCE CONTENT ARTIFACT PERSISTENCE + PROVENANCE PASS key={artifact_key}")
    print("WORKFORCE CONTENT PRODUCER AUDIT + RUNTIME BINDING PASS")

    # Exercise Graphic Designer through the same end-to-end worker lifecycle.
    # The provider is deliberately absent; only a tenant-scoped creative request
    # may be persisted and provider_execution must remain not_configured.
    graphic_agent,graphic_version,graphic_definition_id=await governed_agent(
        tenant_id,suffix,owner_id,"graphic-designer",role_code="ai_graphic_designer",tool_name="workforce_create_visual_asset")
    graphic_prompt="Create a clean abstract SaaS launch visual for the product dashboard"
    graphic_item=await work_item(tenant_id,graphic_agent,suffix,"graphic-designer",request_text=graphic_prompt)
    assert req("POST",f"/work-items/{graphic_item}/assign/agent",{"agent_instance_id":str(graphic_agent)},token)[0]==200
    assert req("POST",f"/work-items/{graphic_item}/dispatch",token=token)[0]==200
    graphic_work,graphic_run=await wait_result(graphic_item)
    assert graphic_work.status is WorkItemStatus.SUCCEEDED and graphic_run and graphic_run.status=="success", (graphic_work.status,graphic_run.error_message if graphic_run else None)
    assert graphic_run.agent_instance_id==graphic_agent and graphic_run.employee_version_id==graphic_version
    await verify_audit(tenant_id,graphic_run.id,tool_name="workforce_create_visual_asset",tool_call_id="e2e-workforce-create-visual-asset-1")
    creative_keys=get_storage_backend().list_prefix(f"{tenant_id}/")
    creative_payloads=[]
    for key in creative_keys:
        if "creative-" in key and key.endswith(".json"):
            payload=workforce_semantic_domains._read_json(str(tenant_id),key)
            if payload.get("prompt")==graphic_prompt:
                creative_payloads.append((key,payload))
    assert len(creative_payloads)==1, f"expected one persisted creative request for prompt, got {len(creative_payloads)}"
    creative_key,creative=creative_payloads[0]
    assert creative["kind"]=="creative_asset_request" and creative["status"]=="draft"
    assert creative["provenance"]["tenant_id"]==str(tenant_id)
    assert creative["provider_execution"]=="not_configured"
    assert creative["approval_status"]=="not_required"
    async with AsyncSessionLocal() as db:
        graphic_binding=(await db.execute(select(AgentRuntimeBinding).where(
            AgentRuntimeBinding.tenant_id==tenant_id,
            AgentRuntimeBinding.agent_definition_id==graphic_definition_id,
            AgentRuntimeBinding.employee_version_id==graphic_version,
            AgentRuntimeBinding.is_active.is_(True),
        ))).scalar_one_or_none()
        assert graphic_binding is not None
    print("WORKFORCE GRAPHIC DESIGNER WORKITEM -> DISPATCH -> WORKER -> RUN PASS")
    print(f"WORKFORCE GRAPHIC REQUEST PERSISTENCE + PROVENANCE PASS key={creative_key}")
    print("WORKFORCE GRAPHIC PROVIDER BOUNDARY PASS provider_execution=not_configured")
    print("WORKFORCE GRAPHIC DESIGNER AUDIT + RUNTIME BINDING PASS")

    # Certify a second routine Content Producer operation through its own
    # WorkItem -> dispatch -> worker -> Run path, not just a direct tool call.
    caption_agent,caption_version,caption_definition_id=await governed_agent(
        tenant_id,suffix,owner_id,"content-caption",role_code="ai_content_producer",tool_name="workforce_produce_social_caption")
    caption_title="Semantic E2E governed social caption"
    caption_item=await work_item(tenant_id,caption_agent,suffix,"content-caption",request_text=f"Produce a social caption titled {caption_title}")
    assert req("POST",f"/work-items/{caption_item}/assign/agent",{"agent_instance_id":str(caption_agent)},token)[0]==200
    assert req("POST",f"/work-items/{caption_item}/dispatch",token=token)[0]==200
    caption_work,caption_run=await wait_result(caption_item)
    assert caption_work.status is WorkItemStatus.SUCCEEDED and caption_run and caption_run.status=="success", (caption_work.status,caption_run.error_message if caption_run else None)
    assert caption_run.agent_instance_id==caption_agent and caption_run.employee_version_id==caption_version
    await verify_audit(tenant_id,caption_run.id,tool_name="workforce_produce_social_caption",tool_call_id="e2e-workforce-produce-social-caption-1")
    caption_payloads=[]
    for key in get_storage_backend().list_prefix(f"{tenant_id}/"):
        if "content-" in key and key.endswith(".json"):
            payload=workforce_semantic_domains._read_json(str(tenant_id),key)
            if payload.get("title")==caption_title:
                caption_payloads.append((key,payload))
    assert len(caption_payloads)==1, f"expected one persisted caption artifact for {caption_title}, got {len(caption_payloads)}"
    caption_key,caption_artifact=caption_payloads[0]
    assert caption_artifact["kind"]=="content_artifact" and caption_artifact["status"]=="draft"
    assert caption_artifact["operation"]=="produce_social_caption"
    assert caption_artifact["provenance"]["tenant_id"]==str(tenant_id)
    assert caption_artifact["provenance"]["provider_execution"]=="not_required"
    assert caption_artifact["approval_status"]=="not_required"
    async with AsyncSessionLocal() as db:
        caption_binding=(await db.execute(select(AgentRuntimeBinding).where(
            AgentRuntimeBinding.tenant_id==tenant_id,
            AgentRuntimeBinding.agent_definition_id==caption_definition_id,
            AgentRuntimeBinding.employee_version_id==caption_version,
            AgentRuntimeBinding.is_active.is_(True),
        ))).scalar_one_or_none()
        assert caption_binding is not None
    print("WORKFORCE CONTENT PRODUCE_SOCIAL_CAPTION FULL WORKITEM LIFECYCLE PASS")
    print(f"WORKFORCE CONTENT CAPTION PERSISTENCE + PROVENANCE PASS key={caption_key}")

    # Certify a second routine Graphic Designer operation through the same
    # canonical lifecycle; provider execution must still remain unconfigured.
    revise_agent,revise_version,revise_definition_id=await governed_agent(
        tenant_id,suffix,owner_id,"graphic-revise",role_code="ai_graphic_designer",tool_name="workforce_revise_visual_asset")
    revise_prompt="Revise the existing SaaS dashboard launch visual to use a calmer palette"
    revise_item=await work_item(tenant_id,revise_agent,suffix,"graphic-revise",request_text=revise_prompt)
    assert req("POST",f"/work-items/{revise_item}/assign/agent",{"agent_instance_id":str(revise_agent)},token)[0]==200
    assert req("POST",f"/work-items/{revise_item}/dispatch",token=token)[0]==200
    revise_work,revise_run=await wait_result(revise_item)
    assert revise_work.status is WorkItemStatus.SUCCEEDED and revise_run and revise_run.status=="success", (revise_work.status,revise_run.error_message if revise_run else None)
    assert revise_run.agent_instance_id==revise_agent and revise_run.employee_version_id==revise_version
    await verify_audit(tenant_id,revise_run.id,tool_name="workforce_revise_visual_asset",tool_call_id="e2e-workforce-revise-visual-asset-1")
    revise_payloads=[]
    for key in get_storage_backend().list_prefix(f"{tenant_id}/"):
        if "creative-" in key and key.endswith(".json"):
            payload=workforce_semantic_domains._read_json(str(tenant_id),key)
            if payload.get("prompt")==revise_prompt:
                revise_payloads.append((key,payload))
    assert len(revise_payloads)==1, f"expected one persisted creative revision request, got {len(revise_payloads)}"
    revise_key,revise_artifact=revise_payloads[0]
    assert revise_artifact["kind"]=="creative_asset_request" and revise_artifact["status"]=="draft"
    assert revise_artifact["operation"]=="revise_visual_asset"
    assert revise_artifact["provenance"]["tenant_id"]==str(tenant_id)
    assert revise_artifact["provider_execution"]=="not_configured"
    assert revise_artifact["approval_status"]=="not_required"
    async with AsyncSessionLocal() as db:
        revise_binding=(await db.execute(select(AgentRuntimeBinding).where(
            AgentRuntimeBinding.tenant_id==tenant_id,
            AgentRuntimeBinding.agent_definition_id==revise_definition_id,
            AgentRuntimeBinding.employee_version_id==revise_version,
            AgentRuntimeBinding.is_active.is_(True),
        ))).scalar_one_or_none()
        assert revise_binding is not None
    print("WORKFORCE GRAPHIC DESIGNER REVISE_VISUAL_ASSET FULL WORKITEM LIFECYCLE PASS")
    print(f"WORKFORCE GRAPHIC REVISION PERSISTENCE + PROVIDER BOUNDARY PASS key={revise_key}")

    # Certify deterministic content QA through the canonical WorkItem lifecycle.
    # This proves report persistence/audit/runtime binding, not factual or brand review.
    qa_agent,qa_version,qa_definition_id=await governed_agent(
        tenant_id,suffix,owner_id,"content-qa",role_code="ai_content_producer",tool_name="workforce_content_qa")
    qa_title="Semantic E2E QA article"
    qa_item=await work_item(tenant_id,qa_agent,suffix,"content-qa",request_text=f"Run content QA on the article titled {qa_title}")
    assert req("POST",f"/work-items/{qa_item}/assign/agent",{"agent_instance_id":str(qa_agent)},token)[0]==200
    assert req("POST",f"/work-items/{qa_item}/dispatch",token=token)[0]==200
    qa_work,qa_run=await wait_result(qa_item)
    assert qa_work.status is WorkItemStatus.SUCCEEDED and qa_run and qa_run.status=="success", (qa_work.status,qa_run.error_message if qa_run else None)
    assert qa_run.agent_instance_id==qa_agent and qa_run.employee_version_id==qa_version
    await verify_audit(tenant_id,qa_run.id,tool_name="workforce_content_qa",tool_call_id="e2e-workforce-content-qa-1")
    qa_payloads=[]
    for key in get_storage_backend().list_prefix(f"{tenant_id}/"):
        if "content-qa-" in key and key.endswith(".json"):
            payload=workforce_semantic_domains._read_json(str(tenant_id),key)
            if payload.get("title")==qa_title:
                qa_payloads.append((key,payload))
    assert len(qa_payloads)==1, f"expected one persisted content QA report for {qa_title}, got {len(qa_payloads)}"
    qa_key,qa_report=qa_payloads[0]
    assert qa_report["kind"]=="content_qa_report" and qa_report["status"]=="passed"
    assert qa_report["operation"]=="content_qa"
    assert qa_report["provenance"]["tenant_id"]==str(tenant_id)
    assert qa_report["provenance"]["provider_execution"]=="not_required"
    assert {item["id"] for item in qa_report["checks"]}=={"title_present","body_present","placeholder_text_absent"}
    assert qa_report["findings"]==[]
    async with AsyncSessionLocal() as db:
        qa_binding=(await db.execute(select(AgentRuntimeBinding).where(
            AgentRuntimeBinding.tenant_id==tenant_id,
            AgentRuntimeBinding.agent_definition_id==qa_definition_id,
            AgentRuntimeBinding.employee_version_id==qa_version,
            AgentRuntimeBinding.is_active.is_(True),
        ))).scalar_one_or_none()
        assert qa_binding is not None
    print("WORKFORCE CONTENT QA FULL WORKITEM LIFECYCLE PASS")
    print(f"WORKFORCE CONTENT QA REPORT PERSISTENCE + PROVENANCE PASS key={qa_key}")
    print("WORKFORCE CONTENT QA STRUCTURAL LIMITATIONS + PROVIDER BOUNDARY PASS")

    wrong,_,_=await governed_agent(
        tenant_id,
        suffix,
        owner_id,
        "wrong-role",
        role_code="ai_marketing_advertising_manager",
    )
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
    try:
        req("POST",f"/work-items/{wid}/dispatch",token=token)
    except AssertionError as exc:
        assert "HTTP 422" in str(exc) and "agent_governance_fingerprint_mismatch" in str(exc), str(exc)
        print("WORKFORCE SEMANTIC STALE-CAPABILITY DENIAL REAL-STACK PASS")
    else:
        raise AssertionError("stale capability drift unexpectedly passed dispatch")

    async with AsyncSessionLocal() as db:
        agent=(await db.execute(select(AgentInstance).where(AgentInstance.id==good,AgentInstance.tenant_id==tenant_id))).scalar_one()
        try: await assert_workforce_operation(db,agent=agent,operation="order_execution")
        except Exception as exc:
            assert "approval" in str(exc).lower()
        else: raise AssertionError("approval-required operation was not denied")
    print("WORKFORCE SEMANTIC APPROVAL-REQUIRED DENIAL GOVERNANCE PASS")
    await verify_cross_tenant_assignment(token,tenant_id,good,suffix)

def main():
    suffix=str(time.time_ns())[-10:]
    status,data=req("POST","/auth/register",{"tenant_name":f"Workforce Semantic E2E {suffix}","tenant_slug":f"workforce-semantic-{suffix}","email":f"workforce-semantic-{suffix}@example.com","password":"WorkforceSemanticE2E-2026!","full_name":"Workforce Semantic E2E Owner"})
    assert status==201,data
    token=data["data"]["access_token"]
    status,me=req("GET","/auth/me",token=token); assert status==200,me
    tenant_id=uuid.UUID(str(me["data"]["tenant"]["id"])); owner_id=uuid.UUID(str(me["data"]["user"]["id"]))
    asyncio.run(run_matrix(token,tenant_id,owner_id,suffix))
    print("WORKFORCE SEMANTIC REAL-STACK E2E MATRIX PASS")

if __name__=="__main__":
    try: main()
    except AssertionError as exc: print(f"WORKFORCE SEMANTIC REAL-STACK E2E MATRIX FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

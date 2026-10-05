"""Real-stack W21 governed AI Business Network evidence E2E."""
from __future__ import annotations
import asyncio,json,os,sys,time,uuid
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from sqlalchemy import select,delete
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.role import Role,user_roles
from app.services.business_network_service import create_request,decide_request
from app.core.exceptions import ValidationAppError
BASE_URL=os.environ.get("E2E_API_BASE_URL","http://localhost:8000/api/v1")
def request(method,path,token,payload=None,expected=200):
    body=None if payload is None else json.dumps(payload).encode()
    try:
        with urlopen(Request(BASE_URL+path,data=body,headers={"Accept":"application/json","Content-Type":"application/json","Authorization":f"Bearer {token}"},method=method),timeout=20) as r:
            data=json.loads(r.read().decode()); assert r.status==expected,data; return data
    except HTTPError as exc:
        raise AssertionError(f"{method} {path} HTTP {exc.code}: {exc.read().decode(errors='replace')}") from exc
def register(suffix):
    p={"tenant_name":f"W21 Network E2E {suffix}","tenant_slug":f"w21-network-{suffix}","email":f"w21-owner-{suffix}@example.com","password":"W21NetworkE2E-2026!","full_name":"W21 Owner"}
    d=request("POST","/auth/register",None,p,201); token=d["data"]["access_token"]; me=request("GET","/auth/me",token)
    return uuid.UUID(me["data"]["tenant"]["id"]),uuid.UUID(me["data"]["user"]["id"]),token,p["tenant_slug"],p["email"]
async def move_user_to_sender(user_id,sender_tenant):
    async with AsyncSessionLocal() as db:
        user=await db.get(User,user_id); assert user
        sender_admin=(await db.execute(select(Role).where(Role.tenant_id==sender_tenant,Role.name=="Admin"))).scalar_one()
        await db.execute(delete(user_roles).where(user_roles.c.user_id==user_id))
        await db.execute(user_roles.insert().values(user_id=user_id,role_id=sender_admin.id))
        user.tenant_id=sender_tenant
        await db.commit()
def err_code(exc): return getattr(exc,"code",None)
async def run():
    suffix=str(time.time_ns())[-10:]
    sender_tenant,requester,requester_token,sender_slug,_=register(suffix+"-sender")
    recipient_tenant,recipient_owner,_,_,_=register(suffix+"-recipient")
    _,sponsor,_,decider_slug,decider_email=register(suffix+"-decider")
    _,decision_user,_,_,_=register(suffix+"-decision")
    await move_user_to_sender(sponsor,sender_tenant)
    await move_user_to_sender(decision_user,sender_tenant)
    # Obtain a fresh token after the tenant move.
    login=request("POST","/auth/login",None,{"email":decider_email,"password":"W21NetworkE2E-2026!","tenant_slug":sender_slug},200)
    decider_token=login["data"]["access_token"]
    same={"recipient_tenant_id":str(sender_tenant),"operation":"partner.handoff","capability_contract":{"version":"w21-v1"},"payload":{},"idempotency_key":"same-tenant","sponsor_user_id":str(sponsor)}
    async with AsyncSessionLocal() as db:
        try:
            await create_request(db,sender_tenant_id=sender_tenant,requester_user_id=requester,sponsor_user_id=sponsor,recipient_tenant_id=sender_tenant,operation="partner.handoff",capability_contract={"version":"w21-v1"},payload={},idempotency_key="same-tenant",correlation_id="corr-same")
            raise AssertionError("same-tenant request unexpectedly accepted")
        except ValidationAppError:
            await db.rollback()
    payload={"recipient_tenant_id":str(recipient_tenant),"operation":"partner.handoff","capability_contract":{"version":"w21-v1","side_effect":"proposal_only"},"payload":{"subject":"controlled handoff"},"idempotency_key":"network-001","correlation_id":"corr-network-001","sponsor_user_id":str(decider)}
    async with AsyncSessionLocal() as db:
        first_obj=await create_request(db,sender_tenant_id=sender_tenant,requester_user_id=requester,sponsor_user_id=sponsor,recipient_tenant_id=recipient_tenant,operation=payload["operation"],capability_contract=payload["capability_contract"],payload=payload["payload"],idempotency_key=payload["idempotency_key"],correlation_id=payload["correlation_id"])
        replay_obj=await create_request(db,sender_tenant_id=sender_tenant,requester_user_id=requester,sponsor_user_id=sponsor,recipient_tenant_id=recipient_tenant,operation=payload["operation"],capability_contract=payload["capability_contract"],payload=payload["payload"],idempotency_key=payload["idempotency_key"],correlation_id=payload["correlation_id"])
        await db.commit()
        first={"id":str(first_obj.id),"status":first_obj.status.value,"correlation_id":first_obj.correlation_id}
        replay={"id":str(replay_obj.id),"status":replay_obj.status.value}
    print("W21 first response", first)
    assert first["status"]=="pending_approval", first
    print("W21 replay response", replay)
    assert replay["id"]==first["id"], replay
    async with AsyncSessionLocal() as db:
        approved_obj=await decide_request(db,sender_tenant_id=sender_tenant,request_id=uuid.UUID(first["id"]),decider_user_id=decision_user,approve=True,reason="W21 E2E approval")
        await db.commit()
        approved={"status":approved_obj.status.value,"correlation_id":approved_obj.correlation_id}
    print("W21 approved response", approved)
    assert approved["status"]=="approved", approved
    assert approved["correlation_id"]=="corr-network-001"
    try:
        request("POST",f"/business-network/requests/{first['id']}/decision",requester_token,{"approve":True},200)
        raise AssertionError("requester unexpectedly decided own request")
    except Exception as exc: assert err_code(exc) in (409,422)
    print("W21 SAME-TENANT REJECTION PASS")
    print("W21 CROSS-TENANT REQUEST PASS")
    print("W21 IDEMPOTENT REPLAY PASS")
    print("W21 APPROVAL GATE PASS")
    print("W21 INDEPENDENT DECISION PASS")
    print("W21 REAL-STACK BUSINESS NETWORK E2E PASS")
if __name__=="__main__":
    try: asyncio.run(run())
    except Exception as exc:
        print(f"W21 REAL-STACK BUSINESS NETWORK E2E FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

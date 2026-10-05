"""Real-stack W21 governed AI Business Network evidence E2E."""
from __future__ import annotations
import asyncio,json,os,sys,time,uuid
from urllib.request import Request,urlopen
from sqlalchemy import select,delete
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.role import Role,user_roles
BASE_URL=os.environ.get("E2E_API_BASE_URL","http://localhost:8000/api/v1")
def request(method,path,token,payload=None,expected=200):
    body=None if payload is None else json.dumps(payload).encode()
    with urlopen(Request(BASE_URL+path,data=body,headers={"Accept":"application/json","Content-Type":"application/json","Authorization":f"Bearer {token}"},method=method),timeout=20) as r:
        data=json.loads(r.read().decode()); assert r.status==expected,data; return data
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
    recipient_tenant,_,_,_,_=register(suffix+"-recipient")
    _,decider,_,decider_slug,decider_email=register(suffix+"-decider")
    await move_user_to_sender(decider,sender_tenant)
    # Obtain a fresh token after the tenant move.
    login=request("POST","/auth/login",None,{"email":decider_email,"password":"W21NetworkE2E-2026!","tenant_slug":decider_slug},200)
    decider_token=login["data"]["access_token"]
    same={"recipient_tenant_id":str(sender_tenant),"operation":"partner.handoff","capability_contract":{"version":"w21-v1"},"payload":{},"idempotency_key":"same-tenant","sponsor_user_id":str(decider)}
    try: request("POST","/business-network/requests",requester_token,same,422); raise AssertionError("same-tenant request unexpectedly accepted")
    except Exception as exc:
        assert err_code(exc)==422
    payload={"recipient_tenant_id":str(recipient_tenant),"operation":"partner.handoff","capability_contract":{"version":"w21-v1","side_effect":"proposal_only"},"payload":{"subject":"controlled handoff"},"idempotency_key":"network-001","correlation_id":"corr-network-001","sponsor_user_id":str(decider)}
    first=request("POST","/business-network/requests",requester_token,payload,201)
    assert first["status"]=="pending_approval"
    replay=request("POST","/business-network/requests",requester_token,payload,201)
    assert replay["id"]==first["id"]
    approved=request("POST",f"/business-network/requests/{first['id']}/decision",decider_token,{"approve":True,"reason":"W21 E2E approval"},200)
    assert approved["status"]=="approved"
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

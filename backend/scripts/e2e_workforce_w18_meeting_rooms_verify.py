"""Real-stack W18 Virtual Meeting Rooms evidence E2E."""
from __future__ import annotations
import asyncio,json,os,sys,time,uuid
from datetime import datetime,timezone
from urllib.request import Request,urlopen
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
from app.core.database import AsyncSessionLocal
from app.models.employee import Employee,EmployeeVersion
from app.models.meeting import Meeting,MeetingParticipant,MeetingParticipantRole,MeetingStatus
BASE_URL=os.environ.get("E2E_API_BASE_URL","http://localhost:8000/api/v1")

def register(suffix):
    payload=json.dumps({"tenant_name":f"W18 Meeting E2E {suffix}","tenant_slug":f"w18-meeting-{suffix}","email":f"w18-owner-{suffix}@example.com","password":"W18MeetingE2E-2026!","full_name":"W18 CEO"}).encode()
    with urlopen(Request(f"{BASE_URL}/auth/register",data=payload,headers={"Accept":"application/json","Content-Type":"application/json"},method="POST"),timeout=20) as r:
        d=json.loads(r.read().decode()); assert r.status==201,d; token=d["data"]["access_token"]
    with urlopen(Request(f"{BASE_URL}/auth/me",headers={"Accept":"application/json","Authorization":f"Bearer {token}"},method="GET"),timeout=20) as r:
        d=json.loads(r.read().decode()); assert r.status==200,d
    return uuid.UUID(d["data"]["tenant"]["id"]),uuid.UUID(d["data"]["user"]["id"]),token

async def seed(t,owner,suffix):
    async with AsyncSessionLocal() as db:
        e=Employee(tenant_id=t,slug=f"w18-employee-{suffix}",name="W18 Engineer",kind="custom",is_active=True); db.add(e); await db.flush()
        v=EmployeeVersion(employee_id=e.id,version_number=1,is_current=True,input_schema={},output_schema={},prompt_template="W18 fixture",allowed_tools=[],rules={}); db.add(v); await db.flush()
        now=datetime.now(timezone.utc); m=Meeting(tenant_id=t,title="W18 Governed Review",description="Real-stack fixture",status=MeetingStatus.ACTIVE,created_by=owner,scheduled_at=now,started_at=now); db.add(m); await db.flush()
        db.add(MeetingParticipant(tenant_id=t,meeting_id=m.id,employee_id=e.id,role=MeetingParticipantRole.PARTICIPANT,joined_at=now)); await db.commit()
        return m.id,e.id

def get(token,mid):
    with urlopen(Request(f"{BASE_URL}/customer-dashboard/meetings/{mid}",headers={"Accept":"application/json","Authorization":f"Bearer {token}"},method="GET"),timeout=20) as r:
        assert r.status==200; return json.loads(r.read().decode())

def expect404(token,mid):
    try:
        with urlopen(Request(f"{BASE_URL}/customer-dashboard/meetings/{mid}",headers={"Accept":"application/json","Authorization":f"Bearer {token}"},method="GET"),timeout=20) as r:
            raise AssertionError(f"unexpected {r.status}")
    except Exception as exc:
        if getattr(exc,"code",None)!=404: raise

async def run():
    s=str(time.time_ns())[-10:]; t,o,token=register(s); mid,eid=await seed(t,o,s); d=get(token,mid)["data"]
    assert d["contract_version"]=="w18-meeting-v1"
    assert d["meeting"]["status"]=="active"
    assert len(d["participants"])==1
    assert d["participants"][0]["employee_id"]==str(eid)
    assert d["participants"][0]["evidence_status"]=="VERIFIED"
    assert d["evidence_status"]=="UNKNOWN"
    t2,_,tok2=register(s+"-other"); assert t2!=t; expect404(tok2,mid)
    print("W18 MEETING API REAL-STACK PASS")
    print("W18 PARTICIPANT TENANT ISOLATION PASS")
    print("W18 EVIDENCE BOUNDARY PASS")
    print("WORKFORCE W18 VIRTUAL-MEETING-ROOMS REAL-STACK E2E PASS")

if __name__=="__main__":
    try: asyncio.run(run())
    except Exception as exc: print(f"WORKFORCE W18 VIRTUAL-MEETING-ROOMS REAL-STACK E2E FAIL: {exc}",file=sys.stderr); raise SystemExit(1)

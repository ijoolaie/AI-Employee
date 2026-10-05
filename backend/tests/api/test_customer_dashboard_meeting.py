from __future__ import annotations
from datetime import datetime,timezone
from types import SimpleNamespace
from uuid import uuid4
import pytest
from app.api.v1 import customer_dashboard
from app.services import meeting_service

class R:
    def __init__(self,rows): self.rows=rows
    def all(self): return list(self.rows)
class DB:
    def __init__(self,m,p): self.m=m; self.p=p
    async def scalar(self,s): return self.m
    async def execute(self,s): return R(self.p)

@pytest.mark.asyncio
async def test_meeting_service_is_tenant_scoped_and_evidence_first():
    t=uuid4(); mid=uuid4(); eid=uuid4(); now=datetime.now(timezone.utc)
    m=SimpleNamespace(id=mid,tenant_id=t,title="Sprint Review",description="Governed",status=SimpleNamespace(value="active"),scheduled_at=now,started_at=now,ended_at=None,created_at=now,work_item_id=uuid4(),run_id=uuid4())
    e=SimpleNamespace(id=eid,tenant_id=t,name="Engineer",slug="engineer")
    p=SimpleNamespace(id=uuid4(),employee_id=eid,role=SimpleNamespace(value="participant"),joined_at=now,left_at=None)
    out=await meeting_service.get_meeting(DB(m,[(p,e)]),tenant_id=t,meeting_id=mid)
    assert out["contract_version"]=="w18-meeting-v1"
    assert out["meeting"]["status"]=="active"
    assert out["participants"][0]["employee_id"]==str(eid)
    assert out["evidence_status"]=="VERIFIED"

@pytest.mark.asyncio
async def test_customer_meeting_route_passes_authenticated_tenant(monkeypatch):
    t=uuid4(); mid=uuid4(); now=datetime.now(timezone.utc); captured={}
    async def fake(db,*,tenant_id,meeting_id):
        captured.update(db=db,tenant_id=tenant_id,meeting_id=meeting_id)
        return {"contract_version":"w18-meeting-v1","meeting":{"id":str(mid),"title":"Room","description":None,"status":"scheduled","scheduled_at":now,"started_at":None,"ended_at":None,"created_at":now},"participants":[],"evidence_status":"UNKNOWN","evidence_refs":[],"provider_state":"NOT_APPLICABLE"}
    monkeypatch.setattr(customer_dashboard.customer_dashboard_service,"get_meeting",fake)
    response=await customer_dashboard.get_customer_meeting(meeting_id=mid,ctx=SimpleNamespace(tenant_id=t),db=object())
    assert response.success is True
    assert captured["tenant_id"]==t
    assert captured["meeting_id"]==mid

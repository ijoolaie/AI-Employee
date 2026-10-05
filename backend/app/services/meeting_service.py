from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.employee import Employee
from app.models.meeting import Meeting, MeetingParticipant

async def get_meeting(db: AsyncSession, *, tenant_id, meeting_id):
    meeting=await db.scalar(select(Meeting).where(Meeting.tenant_id==tenant_id,Meeting.id==meeting_id))
    if meeting is None: raise NotFoundError("Meeting not found")
    result=await db.execute(select(MeetingParticipant,Employee).join(Employee,Employee.id==MeetingParticipant.employee_id).where(MeetingParticipant.tenant_id==tenant_id,MeetingParticipant.meeting_id==meeting_id,Employee.tenant_id==tenant_id).order_by(MeetingParticipant.created_at.asc()))
    participants=[{"id":str(p.id),"employee_id":str(e.id),"employee_name":e.name,"employee_slug":e.slug,"role":p.role.value,"joined_at":p.joined_at,"left_at":p.left_at,"evidence_status":"VERIFIED"} for p,e in result.all()]
    refs=[]
    if meeting.work_item_id is not None: refs.append("work_item:"+str(meeting.work_item_id))
    if meeting.run_id is not None: refs.append("run:"+str(meeting.run_id))
    return {"contract_version":"w18-meeting-v1","meeting":{"id":str(meeting.id),"title":meeting.title,"description":meeting.description,"status":meeting.status.value,"scheduled_at":meeting.scheduled_at,"started_at":meeting.started_at,"ended_at":meeting.ended_at,"created_at":meeting.created_at},"participants":participants,"evidence_status":"VERIFIED" if refs else "UNKNOWN","evidence_refs":refs,"provider_state":"NOT_APPLICABLE"}

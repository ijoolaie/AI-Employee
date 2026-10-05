from datetime import datetime
from pydantic import BaseModel, Field

class CustomerOfficeWorkItemResponse(BaseModel):
    id: str
    title: str
    status: str

class CustomerOfficeEmployeeResponse(BaseModel):
    id: str
    name: str
    slug: str
    avatar_url: str | None
    kind: str
    is_active: bool
    presentation_state: str
    latest_run_id: str | None
    latest_run_status: str | None
    latest_run_created_at: datetime | None
    current_work_item: CustomerOfficeWorkItemResponse | None

class CustomerOfficeApprovalResponse(BaseModel):
    id: str
    workflow_run_id: str
    workflow_step_run_id: str
    employee_id: str | None
    employee_name: str | None
    step_key: str
    status: str
    created_at: datetime
    expires_at: datetime | None

class CustomerOfficeResponse(BaseModel):
    office_state: str
    hq_tier: str = "STARTER"
    hq_metrics: dict = Field(default_factory=dict)
    employee_count: int
    working_count: int
    waiting_count: int
    idle_count: int
    blocked_count: int
    escalated_count: int
    employees: list[CustomerOfficeEmployeeResponse]
    pending_approvals: list[CustomerOfficeApprovalResponse]
    generated_at: datetime

class CustomerDashboardResponse(BaseModel):
    employee_count: int
    active_employee_count: int
    workflow_count: int
    active_workflow_count: int
    workflow_run_count: int
    running_workflow_run_count: int
    successful_workflow_run_count: int
    failed_workflow_run_count: int
    pending_approval_count: int
    active_schedule_count: int
    active_webhook_count: int
    recent_runs: list[dict]
    usage: dict
    health: dict
    generated_at: datetime


class CustomerCareerIndicatorResponse(BaseModel):
    code: str
    label: str
    value: int | float | str | None
    evidence_status: str
    evidence_refs: list[str] = Field(default_factory=list)


class CustomerCareerWorkItemResponse(BaseModel):
    id: str
    title: str
    status: str
    completed_at: datetime | None
    run_id: str


class CustomerCareerResponse(BaseModel):
    contract_version: str
    employee: dict
    tenure: dict
    work_history: list[CustomerCareerWorkItemResponse]
    indicators: list[CustomerCareerIndicatorResponse]
    achievements: list[dict] = Field(default_factory=list)


class CustomerMeetingParticipantResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    employee_slug: str
    role: str
    joined_at: datetime | None
    left_at: datetime | None
    evidence_status: str

class CustomerMeetingResponse(BaseModel):
    contract_version: str
    meeting: dict
    participants: list[CustomerMeetingParticipantResponse]
    evidence_status: str
    evidence_refs: list[str] = Field(default_factory=list)
    provider_state: str

from datetime import datetime
from pydantic import BaseModel

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

class CustomerOfficeResponse(BaseModel):
    office_state: str
    employee_count: int
    working_count: int
    waiting_count: int
    idle_count: int
    blocked_count: int
    escalated_count: int
    employees: list[CustomerOfficeEmployeeResponse]
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

from datetime import datetime
from pydantic import BaseModel

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

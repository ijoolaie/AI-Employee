from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkflowParallelBranch(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    steps: list[dict[str, Any]] = Field(min_length=1, max_length=20)


class WorkflowStepDefinition(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    type: str = "employee"
    employee_id: UUID | None = None
    input_mapping: dict[str, str] = Field(default_factory=dict)
    output_key: str | None = None
    retry_max: int = Field(default=0, ge=0, le=5)
    condition: dict[str, Any] | None = None
    condition_value: bool = True
    condition_ref: str | None = None
    timeout_seconds: int = Field(default=86400, ge=1, le=2592000)
    message: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    branches: list[WorkflowParallelBranch] = Field(default_factory=list, max_length=20)

    @field_validator("type")
    @classmethod
    def supported_type(cls, value: str) -> str:
        if value not in {"employee", "condition", "approval", "parallel"}:
            raise ValueError("supported workflow step types: employee, condition, approval, parallel")
        return value

    @field_validator("employee_id")
    @classmethod
    def employee_required_for_employee_step(cls, value: UUID | None, info):
        if info.data.get("type", "employee") == "employee" and value is None:
            raise ValueError("employee_id is required for employee steps")
        return value


class WorkflowCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    steps: list[WorkflowStepDefinition] = Field(min_length=1, max_length=50)
    trigger_type: str = "manual"
    max_runtime_seconds: int | None = Field(default=None, ge=1, le=2592000)

    @field_validator("trigger_type")
    @classmethod
    def trigger_supported(cls, value: str) -> str:
        if value not in {"manual", "schedule", "event"}:
            raise ValueError("supported trigger types: manual, schedule, event")
        return value


class WorkflowVersionCreate(BaseModel):
    steps: list[WorkflowStepDefinition] = Field(min_length=1, max_length=50)
    trigger_type: str = "manual"
    max_runtime_seconds: int | None = Field(default=None, ge=1, le=2592000)
    activate: bool = True

    @field_validator("trigger_type")
    @classmethod
    def trigger_supported(cls, value: str) -> str:
        if value not in {"manual", "schedule", "event"}:
            raise ValueError("supported trigger types: manual, schedule, event")
        return value


class WorkflowVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    version_number: int
    is_current: bool
    trigger_type: str
    config: dict[str, Any]
    execution_contract: dict[str, Any]
    content_hash: str | None
    created_by: UUID | None
    created_at: datetime


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    name: str
    is_active: bool
    current_version_id: UUID | None = None
    created_at: datetime


class WorkflowRunCreate(BaseModel):
    workflow_version_id: UUID | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    workflow_version_id: UUID
    status: str
    context: dict[str, Any]
    output_data: dict[str, Any] | None
    error: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None
    deadline_at: datetime | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    created_at: datetime


class WorkflowScheduleCreate(BaseModel):
    cron_expression: str = Field(min_length=1, max_length=100)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)

class WorkflowScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    cron_expression: str
    timezone: str
    is_active: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_workflow_run_id: UUID | None

class WorkflowEventTriggerCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=120)

class WorkflowEventTriggerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    event_type: str
    is_active: bool
    created_at: datetime
    secret_rotated_at: datetime | None = None

class WorkflowEventTriggerUpdate(BaseModel):
    is_active: bool | None = None

class WorkflowEventDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    trigger_id: UUID
    event_id: str
    event_type: str
    status: str
    workflow_run_id: UUID | None
    attempts: int
    error: dict[str, Any] | None
    received_at: datetime
    processed_at: datetime | None

class WorkflowEventTriggerCreatedResponse(WorkflowEventTriggerResponse):
    webhook_secret: str
    webhook_url: str

class WorkflowEventTriggerRotatedResponse(WorkflowEventTriggerResponse):
    webhook_secret: str
    webhook_url: str
    secret_rotated_at: datetime


class WorkflowApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=2000)

class WorkflowApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    step_key: str
    status: str
    requested_by: UUID | None
    decided_by: UUID | None
    decision_reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_", serialization_alias="metadata")
    expires_at: datetime | None
    decided_at: datetime | None
    created_at: datetime


class WorkflowReplayRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)


class WorkflowCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)

class WorkflowScheduleUpdate(BaseModel):
    cron_expression: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None

class WorkflowScheduleListResponse(WorkflowScheduleResponse):
    workflow_name: str

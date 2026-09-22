from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

class GuardrailsResponse(BaseModel):
    employee_id: UUID
    version_id: UUID
    rules: dict[str, Any]

class GuardrailsUpdate(BaseModel):
    allowed_tools: list[str] | None = None
    rules: dict[str, Any] = Field(default_factory=dict)

class EmployeeTemplate(BaseModel):
    code: str
    name: str
    name_fa: str
    description: str
    description_fa: str
    purpose: str
    purpose_fa: str
    category: str
    input_contract: str
    output_contract: str
    dependencies: list[str] = Field(default_factory=list)
    example: str
    example_fa: str
    version: str
    min_platform_version: str
    kind: str = "custom"
    allowed_tools: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)
    prompt_template: str = ""

class AnalyticsResponse(BaseModel):
    conversations: int
    ai_resolved: int
    human_handoffs: int
    runs: int
    successful_runs: int
    orders: int
    revenue: float
    influenced_orders: int
    influenced_revenue: float
    ai_resolution_rate: float
    handoff_rate: float

class PrivacyExport(BaseModel):
    customer: dict[str, Any]
    conversations: list[dict[str, Any]]
    messages: list[dict[str, Any]]
    orders: list[dict[str, Any]]

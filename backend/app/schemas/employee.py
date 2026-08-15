"""Pydantic schemas for Employee / EmployeeVersion endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmployeeVersionCreate(BaseModel):
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    prompt_template: str = ""
    allowed_tools: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)


class EmployeeCreate(EmployeeVersionCreate):
    slug: str
    name: str
    kind: str = "custom"  # tenant-created Employees are Custom by definition


class EmployeeVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    is_current: bool
    allowed_tools: list[str]
    created_at: datetime


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    kind: str
    is_active: bool
    created_at: datetime


class ToolResponse(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    side_effects: bool
    required_permission: str = "run.execute"
    requires_approval: bool = False

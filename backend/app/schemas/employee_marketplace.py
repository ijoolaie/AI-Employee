from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EmployeeMarketplacePackageCreate(BaseModel):
    source_agent_template_id: UUID
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=255)
    version: int = Field(default=1, ge=1)
    description: str | None = Field(default=None, max_length=4000)
    visibility: str = Field(default="public", pattern="^(private|unlisted|public)$")
    skill_package_ids: list[str] = Field(default_factory=list)
    workflow_refs: list[str] = Field(default_factory=list)
    visual_pack: dict = Field(default_factory=dict)


class EmployeeMarketplacePackageRead(BaseModel):
    id: UUID
    owner_tenant_id: UUID
    source_agent_template_id: UUID
    slug: str
    name: str
    description: str | None
    version: int
    status: str
    visibility: str
    risk_tier: int
    employee_manifest: dict
    permission_manifest: dict
    skill_package_ids: list
    workflow_refs: list
    visual_pack: dict
    published_at: datetime | None


class EmployeeMarketplaceInstallRequest(BaseModel):
    sponsor_user_id: UUID


class EmployeeMarketplaceInstallationRead(BaseModel):
    id: UUID
    buyer_tenant_id: UUID
    package_id: UUID
    imported_agent_definition_id: UUID
    imported_agent_template_id: UUID
    sponsor_user_id: UUID
    status: str
    provider_execution_status: str
    installed_at: datetime
    revoked_at: datetime | None

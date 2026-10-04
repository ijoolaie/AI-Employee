from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SkillMarketplacePublicationCreate(BaseModel):
    skill_package_id: UUID
    visibility: str = Field(default="private", pattern="^(private|unlisted|public)$")
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=2000)


class SkillMarketplacePublicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_tenant_id: UUID
    skill_package_id: UUID
    visibility: str
    title: str
    summary: str | None
    published_by: UUID | None
    published_at: datetime
    customer_acceptance: str = "not_implied"
    installation: str = "not_implied"
    execution_authority: str = "not_implied"
    trust_basis: str = "recorded_evidence_only"

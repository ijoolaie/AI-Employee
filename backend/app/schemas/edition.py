"""Schemas for runtime vendor/reseller/customer control-plane operations."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChildTenantProvisionRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")
    admin_email: str = Field(min_length=3, max_length=320)
    admin_password: str = Field(min_length=12, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    vendor_release_tag: str | None = Field(default=None, max_length=80)
    delivery_revision: str | None = Field(default=None, max_length=120)


class TenantSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    tenant_kind: str
    parent_tenant_id: UUID | None
    vendor_release_tag: str | None
    delivery_revision: str | None

    model_config = {"from_attributes": True}


class EntitlementDelegationRequest(BaseModel):
    feature_code: str = Field(min_length=2, max_length=120)
    quota_limit: int | None = Field(default=None, ge=0)


class EntitlementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    delegated_from_tenant_id: UUID | None
    feature_code: str
    quota_limit: int | None
    quota_used: int
    is_enabled: bool

    model_config = {"from_attributes": True}


class SupportEscalationRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5, max_length=10000)


class SupportEscalationResponse(BaseModel):
    id: UUID
    from_tenant_id: UUID
    to_tenant_id: UUID
    status: str
    subject: str
    description: str

    model_config = {"from_attributes": True}

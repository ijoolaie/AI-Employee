"""Schemas for runtime vendor/reseller/customer control-plane operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class ChildTenantProvisionRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")
    admin_email: EmailStr

    model_config = {"extra": "forbid"}
    full_name: str | None = Field(default=None, max_length=255)
    vendor_release_tag: str | None = Field(default=None, max_length=80)
    delivery_revision: str | None = Field(default=None, max_length=120)


class TenantSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
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


class LicenseIssueRequest(BaseModel):
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)
    feature_codes: list[str] = Field(default_factory=list, max_length=100)
    metadata: dict = Field(default_factory=dict)

    @field_validator("feature_codes")
    @classmethod
    def validate_feature_codes(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("feature codes must not be blank")
        return normalized


class LicenseRevokeRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class LicenseListResponse(BaseModel):
    """Safe license summary for list views; never returns the bearer license key."""
    id: UUID
    issuer_tenant_id: UUID
    tenant_id: UUID
    edition: str
    status: str
    issued_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    revocation_reason: str | None
    feature_codes: list[str]

    model_config = {"from_attributes": True}


class LicenseResponse(BaseModel):
    id: UUID
    license_key: str
    issuer_tenant_id: UUID
    tenant_id: UUID
    edition: str
    status: str
    issued_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    revocation_reason: str | None
    feature_codes: list[str]

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


class SupportEscalationStatusRequest(BaseModel):
    status: str = Field(pattern=r"^(open|in_progress|resolved)$")


class SupportEscalationMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    attachment_file_ids: list[UUID] = Field(default_factory=list, max_length=5)


class SupportEscalationMessageAttachmentResponse(BaseModel):
    id: UUID
    file_id: UUID
    filename: str
    content_type: str | None
    size_bytes: int
    created_at: datetime


class SupportEscalationMessageResponse(BaseModel):
    id: UUID
    escalation_id: UUID
    author_tenant_id: UUID
    author_user_id: UUID | None
    body: str
    created_at: datetime
    attachments: list[SupportEscalationMessageAttachmentResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TenantInvitationCreateRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    role_ids: list[UUID] = Field(min_length=1, max_length=20)
    expires_in_days: int = Field(default=7, ge=1, le=30)


class TenantInvitationResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    token: str
    expires_at: datetime


class TenantInvitationRevokedResponse(BaseModel):
    id: UUID
    revoked_at: datetime


class ChildTenantProvisionResponse(BaseModel):
    tenant: TenantSummary
    user_id: UUID
    invitation_id: UUID
    invitation_token: str
    invitation_expires_at: datetime

"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    tenant_name: str = Field(..., min_length=2, max_length=255)
    tenant_slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str = Field(..., min_length=2, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    tenant_id: UUID
    is_active: bool
    is_platform_admin: bool

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserResponse
    tenant: TenantResponse

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    tenant_slug: str = Field(min_length=1, max_length=120)

class ForgotPasswordResponse(BaseModel):
    message: str

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    password: str = Field(min_length=8, max_length=128)

class ResetPasswordResponse(BaseModel):
    message: str

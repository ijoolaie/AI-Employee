"""Auth endpoints: register, login, refresh, me."""

from fastapi import APIRouter, status

from app.core.deps import CurrentContext, DbSession
from app.schemas.auth import (
    ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    TenantResponse,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import APIResponse
from app.services import auth_service, password_reset_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: RegisterRequest, db: DbSession):
    tenant, user = await auth_service.register_tenant_and_user(db, payload)
    tokens = auth_service.issue_tokens(user)
    return APIResponse(success=True, data=tokens)


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(payload: LoginRequest, db: DbSession):
    user = await auth_service.authenticate_user(db, payload)
    tokens = auth_service.issue_tokens(user)
    return APIResponse(success=True, data=tokens)


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh(payload: RefreshRequest, db: DbSession):
    tokens = await auth_service.refresh_tokens(db, payload.refresh_token)
    return APIResponse(success=True, data=tokens)


@router.get("/me", response_model=APIResponse[MeResponse])
async def me(ctx: CurrentContext):
    data = MeResponse(
        user=UserResponse.model_validate(ctx.user),
        tenant=TenantResponse.model_validate(ctx.tenant),
    )
    return APIResponse(success=True, data=data)


@router.post("/forgot-password", response_model=APIResponse[ForgotPasswordResponse])
async def forgot_password(payload: ForgotPasswordRequest, db: DbSession):
    message = await password_reset_service.request_reset(db, email=payload.email, tenant_slug=payload.tenant_slug)
    await db.commit()
    return APIResponse(success=True, data=ForgotPasswordResponse(message=message))


@router.post("/reset-password", response_model=APIResponse[ResetPasswordResponse])
async def reset_password(payload: ResetPasswordRequest, db: DbSession):
    await password_reset_service.reset_password(db, raw_token=payload.token, password=payload.password)
    await db.commit()
    return APIResponse(success=True, data=ResetPasswordResponse(message="Password reset successfully. Please sign in again."))

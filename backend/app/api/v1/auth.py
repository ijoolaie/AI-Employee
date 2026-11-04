"""Auth endpoints: register, login, refresh, me."""

from fastapi import APIRouter, status

from app.core.deps import CurrentContext, DbSession
from app.schemas.auth import (
    AcceptInvitationRequest,
    InvitationAcceptanceResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    RegistrationPendingResponse,
    TenantResponse,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import APIResponse
from app.services import auth_service, password_change_service, password_reset_service, tenant_invitation_service, tenant_access_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=APIResponse[RegistrationPendingResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def register(payload: RegisterRequest, db: DbSession):
    tenant, _user = await auth_service.register_tenant_and_user(db, payload)
    await db.commit()
    return APIResponse(success=True, data=RegistrationPendingResponse(
        tenant_id=tenant.id,
        message="Registration received. You can sign in to complete billing; workspace access is enabled after an approved payment or operator Demo grant.",
    ))


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
async def me(ctx: CurrentContext, db: DbSession):
    permissions = {
        permission.code
        for role in ctx.user.roles
        if role.tenant_id == ctx.tenant_id
        for permission in role.permissions
    }
    if ctx.api_key_scopes is not None:
        permissions &= set(ctx.api_key_scopes)
    data = MeResponse(
        user=UserResponse.model_validate(ctx.user).model_copy(update={"permissions": sorted(permissions)}),
        tenant=TenantResponse.model_validate(ctx.tenant).model_copy(update={"access_granted": await tenant_access_service.tenant_has_access(db, tenant=ctx.tenant)}),
    )
    return APIResponse(success=True, data=data)


@router.post("/change-password", response_model=APIResponse[ChangePasswordResponse])
async def change_password(payload: ChangePasswordRequest, ctx: CurrentContext, db: DbSession):
    await password_change_service.change_password(
        db,
        user=ctx.user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    await db.commit()
    return APIResponse(
        success=True,
        data=ChangePasswordResponse(
            message="Password changed successfully. Please sign in again."
        ),
    )


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


@router.post("/invitations/accept", response_model=APIResponse[InvitationAcceptanceResponse])
async def accept_invitation(payload: AcceptInvitationRequest, db: DbSession):
    invitation, access_granted = await tenant_invitation_service.accept_invitation(
        db, raw_token=payload.token, password=payload.password,
    )
    await db.commit()
    message = (
        "Invitation accepted. You can sign in now."
        if access_granted
        else "Invitation accepted. You can sign in to complete billing; workspace access requires an approved payment or Demo grant."
    )
    return APIResponse(success=True, data=InvitationAcceptanceResponse(access_granted=access_granted, message=message))

"""FastAPI dependencies: DB session, current user, tenant context."""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.middleware import RequestContextMiddleware
from app.core.security import decode_token
from app.models.user import User
from app.models.api_key import APIKey
from app.services.api_key_service import verify_key
from app.models.tenant import Tenant
from app.models.role import Role

security_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


class TenantContext:
    """Request-scoped tenant + user context. Never trust client-sent tenant_id."""

    def __init__(self, user: User, tenant: Tenant, *, api_key_id: UUID | None = None, api_key_scopes: list[str] | None = None):
        self.user = user
        self.tenant = tenant
        self.api_key_id = api_key_id
        self.api_key_scopes = api_key_scopes

    @property
    def tenant_id(self) -> UUID:
        return self.tenant.id

    @property
    def user_id(self) -> UUID:
        return self.user.id


async def get_current_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    api_key: Annotated[str | None, Depends(api_key_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantContext:
    if api_key:
        key_row = await verify_key(db, api_key)
        if key_row is None:
            raise HTTPException(status_code=401, detail="Invalid or expired API key")
        user_result = await db.execute(
            select(User).options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == key_row.created_by, User.tenant_id == key_row.tenant_id)
        )
        user = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="API key owner is inactive")
        tenant_result = await db.execute(select(Tenant).where(Tenant.id == key_row.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if tenant is None or tenant.status != "active":
            raise HTTPException(status_code=403, detail="Tenant not available")
        RequestContextMiddleware.bind_identity(str(tenant.id), str(user.id))
        return TenantContext(user=user, tenant=tenant, api_key_id=key_row.id, api_key_scopes=key_row.scopes)

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not user_id or not tenant_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user_result = await db.execute(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    if payload.get("auth_token_version") is not None and payload.get("auth_token_version") != user.auth_token_version:
        raise HTTPException(status_code=401, detail="Session invalidated; please sign in again")
    if str(user.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None or tenant.status != "active":
        raise HTTPException(status_code=403, detail="Tenant not available")
    RequestContextMiddleware.bind_identity(str(tenant.id), str(user.id))
    return TenantContext(user=user, tenant=tenant)


async def has_permission(ctx: TenantContext, permission_code: str) -> bool:
    """Return whether the request has a tenant permission."""
    if ctx.api_key_scopes is not None and permission_code not in set(ctx.api_key_scopes):
        return False
    if ctx.user.is_superuser:
        return True
    return any(
        permission.code == permission_code
        for role in ctx.user.roles
        if role.tenant_id == ctx.tenant_id
        for permission in role.permissions
    )


def require_permission(permission_code: str):
    """FastAPI dependency factory for endpoint-level RBAC enforcement."""
    async def checker(ctx: Annotated[TenantContext, Depends(get_current_context)]) -> TenantContext:
        if not await has_permission(ctx, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission_code}")
        return ctx
    return checker


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentContext = Annotated[TenantContext, Depends(get_current_context)]

EmployeeReadContext = Annotated[TenantContext, Depends(require_permission("employee.read"))]
EmployeeWriteContext = Annotated[TenantContext, Depends(require_permission("employee.write"))]
EmployeeGuardrailsReadContext = Annotated[TenantContext, Depends(require_permission("employee.guardrails.read"))]
EmployeeGuardrailsWriteContext = Annotated[TenantContext, Depends(require_permission("employee.guardrails.write"))]
RunReadContext = Annotated[TenantContext, Depends(require_permission("run.read"))]
RunExecuteContext = Annotated[TenantContext, Depends(require_permission("run.execute"))]
FileReadContext = Annotated[TenantContext, Depends(require_permission("file.read"))]
FileWriteContext = Annotated[TenantContext, Depends(require_permission("file.write"))]
AuditReadContext = Annotated[TenantContext, Depends(require_permission("audit.read"))]
FeedbackCreateContext = Annotated[TenantContext, Depends(require_permission("feedback.create"))]
FeedbackReadContext = Annotated[TenantContext, Depends(require_permission("feedback.read"))]
ApprovalReadContext = Annotated[TenantContext, Depends(require_permission("approval.read"))]
ApprovalDecideContext = Annotated[TenantContext, Depends(require_permission("approval.decide"))]
PrivacyCustomerReadContext = Annotated[TenantContext, Depends(require_permission("privacy.customer.read"))]
PrivacyCustomerExportContext = Annotated[TenantContext, Depends(require_permission("privacy.customer.export"))]
PrivacyCustomerDeleteContext = Annotated[TenantContext, Depends(require_permission("privacy.customer.delete"))]
MemoryReadContext = Annotated[TenantContext, Depends(require_permission("memory.read"))]
MemoryWriteContext = Annotated[TenantContext, Depends(require_permission("memory.write"))]
MemoryDeleteContext = Annotated[TenantContext, Depends(require_permission("memory.delete"))]
WorkflowReadContext = Annotated[TenantContext, Depends(require_permission("workflow.read"))]
WorkflowWriteContext = Annotated[TenantContext, Depends(require_permission("workflow.write"))]
WorkflowExecuteContext = Annotated[TenantContext, Depends(require_permission("workflow.execute"))]
WorkflowCancelContext = Annotated[TenantContext, Depends(require_permission("workflow.cancel"))]
WorkflowApprovalReadContext = Annotated[TenantContext, Depends(require_permission("workflow.approval.read"))]
WorkflowApprovalDecideContext = Annotated[TenantContext, Depends(require_permission("workflow.approval.decide"))]
WorkflowEventReadContext = Annotated[TenantContext, Depends(require_permission("workflow.event.read"))]
WorkflowEventWriteContext = Annotated[TenantContext, Depends(require_permission("workflow.event.write"))]
BillingRefundContext = Annotated[TenantContext, Depends(require_permission("billing.refund"))]
TeamInstallContext = Annotated[TenantContext, Depends(require_permission("team.install"))]
TeamExecuteContext = Annotated[TenantContext, Depends(require_permission("team.execute"))]

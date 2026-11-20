"""FastAPI dependencies: DB session, current user, tenant context."""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
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
from app.services.tenant_access_service import tenant_has_access

security_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


_PORTAL_CONTEXT_DENIED_PREFIXES = (
    "/api/v1/billing",
    "/api/v1/auth",
    "/api/v1/api-keys",
    "/api/v1/tenant-admin",
    "/api/v1/onboarding",
    "/api/v1/world-commerce",
    # Portal context is for tenant data access, never control-plane mutation.
    "/api/v1/edition",
    "/api/v1/admin",
    "/api/v1/operations",
    "/api/v1/usage",
)


def _portal_context_path_is_denied(path: str) -> bool:
    """Keep account/control-plane APIs outside a delegated portal session."""
    if (
        path in {
            "/api/v1/auth/me",
            "/api/v1/operations/audit-logs",
            "/api/v1/operations/metrics",
            "/api/v1/usage/summary",
            "/api/v1/usage/optimization",
            "/api/v1/usage/cost-forecast",
        }
        or path == "/api/v1/operations/dead-letters"
        or path.startswith("/api/v1/operations/dead-letters/")
    ):
        return False
    return path == "/api/v1/analytics/roi" or any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in _PORTAL_CONTEXT_DENIED_PREFIXES
    )


class TenantContext:
    """Request-scoped tenant + user context. Never trust client-sent tenant_id."""

    def __init__(self, user: User, tenant: Tenant, *, api_key_id: UUID | None = None, api_key_scopes: list[str] | None = None):
        self.user = user
        self.tenant = tenant
        self.actor_tenant_id = getattr(user, "tenant_id", tenant.id)
        self.api_key_id = api_key_id
        self.api_key_scopes = api_key_scopes

    @property
    def tenant_id(self) -> UUID:
        return self.tenant.id

    @property
    def user_id(self) -> UUID:
        return self.user.id


async def get_current_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    api_key: Annotated[str | None, Depends(api_key_scheme)],
    db: Annotated[AsyncSession, Depends(get_db, scope="function")],
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
        if not await tenant_has_access(db, tenant=tenant):
            raise HTTPException(status_code=402, detail="Tenant requires an approved paid subscription or active Demo grant")
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

    portal_context_tenant_id = payload.get("portal_context_tenant_id")
    if portal_context_tenant_id is not None:
        if _portal_context_path_is_denied(request.url.path):
            raise HTTPException(status_code=403, detail="Portal context tokens cannot access account, billing, administration, or unscoped endpoints")
        try:
            context_tenant_uuid = UUID(str(portal_context_tenant_id))
            context_grant_uuid = UUID(str(payload["portal_context_grant_id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Invalid portal context token") from exc
        from app.services.portal_access_service import validate_portal_access_grant
        await validate_portal_access_grant(db, actor_user_id=user.id, actor_tenant_id=user.tenant_id, target_tenant_id=context_tenant_uuid, grant_id=context_grant_uuid)
        target_result = await db.execute(select(Tenant).where(Tenant.id == context_tenant_uuid))
        target_tenant = target_result.scalar_one_or_none()
        if target_tenant is None or payload.get("portal_context_kind") != target_tenant.tenant_kind:
            raise HTTPException(status_code=403, detail="Portal context tenant kind mismatch")
        tenant = target_tenant

    billing_only_paths = {
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/billing/subscription"),
        ("GET", "/api/v1/billing/entitlements"),
        ("POST", "/api/v1/billing/checkout"),
        ("POST", "/api/v1/billing/portal"),
    }
    if (request.method, request.url.path) not in billing_only_paths and not await tenant_has_access(db, tenant=tenant):
        raise HTTPException(status_code=402, detail="Tenant requires an approved paid subscription or active Demo grant")
    RequestContextMiddleware.bind_identity(str(tenant.id), str(user.id))
    return TenantContext(user=user, tenant=tenant)


async def has_permission(ctx: TenantContext, permission_code: str) -> bool:
    """Return whether the request has a tenant permission."""
    if ctx.api_key_scopes is not None and permission_code not in set(ctx.api_key_scopes):
        return False
    return any(
        permission.code == permission_code
        for role in ctx.user.roles
        if role.tenant_id == getattr(ctx, "actor_tenant_id", ctx.tenant_id)
        for permission in role.permissions
    )


def require_permission(permission_code: str):
    """FastAPI dependency factory for endpoint-level RBAC enforcement."""
    async def checker(ctx: Annotated[TenantContext, Depends(get_current_context)]) -> TenantContext:
        if not await has_permission(ctx, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission_code}")
        return ctx
    return checker


DbSession = Annotated[AsyncSession, Depends(get_db, scope="function")]
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
BillingManageContext = Annotated[TenantContext, Depends(require_permission("billing.manage"))]
CommerceIntegrationContext = Annotated[TenantContext, Depends(require_permission("commerce.integration.manage"))]
OrdersReadContext = Annotated[TenantContext, Depends(require_permission("orders.read"))]
OrdersCreateContext = Annotated[TenantContext, Depends(require_permission("orders.create"))]
OrdersUpdateContext = Annotated[TenantContext, Depends(require_permission("orders.update"))]
OrdersInvoiceLinkContext = Annotated[TenantContext, Depends(require_permission("orders.invoice_link"))]
SalesReadContext = Annotated[TenantContext, Depends(require_permission("sales.read"))]
SalesCreateContext = Annotated[TenantContext, Depends(require_permission("sales.create"))]
SalesUpdateContext = Annotated[TenantContext, Depends(require_permission("sales.update"))]
CustomerReadContext = Annotated[TenantContext, Depends(require_permission("customers.read"))]
CustomerCreateContext = Annotated[TenantContext, Depends(require_permission("customers.create"))]
CustomerUpdateContext = Annotated[TenantContext, Depends(require_permission("customers.update"))]
InvoiceReadContext = Annotated[TenantContext, Depends(require_permission("invoices.read"))]
InvoiceCreateContext = Annotated[TenantContext, Depends(require_permission("invoices.create"))]
InvoiceUpdateContext = Annotated[TenantContext, Depends(require_permission("invoices.update"))]
InvoiceExportPdfContext = Annotated[TenantContext, Depends(require_permission("invoices.export_pdf"))]
ProductReadContext = Annotated[TenantContext, Depends(require_permission("products.read"))]
ProductCreateContext = Annotated[TenantContext, Depends(require_permission("products.create"))]
ProductUpdateContext = Annotated[TenantContext, Depends(require_permission("products.update"))]
ProductInventoryUpdateContext = Annotated[TenantContext, Depends(require_permission("products.inventory_update"))]
TeamInstallContext = Annotated[TenantContext, Depends(require_permission("team.install"))]
TeamExecuteContext = Annotated[TenantContext, Depends(require_permission("team.execute"))]
APIKeysReadContext = Annotated[TenantContext, Depends(require_permission("api_keys.read"))]
APIKeysCreateContext = Annotated[TenantContext, Depends(require_permission("api_keys.create"))]
APIKeysRevokeContext = Annotated[TenantContext, Depends(require_permission("api_keys.revoke"))]
"""FastAPI dependencies for commercial edition boundaries."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.deps import CurrentContext, DbSession, TenantContext
from app.services.edition_service import require_edition, EDITION_CUSTOMER, EDITION_RESELLER, EDITION_VENDOR

# Scope names are an explicit contract for API-key access to the commercial
# control plane. The edition dependency still enforces tenant kind and admin
# status; these scopes narrow API keys to individual operations.
EDITION_SCOPE_ALLOWLIST_BY_KIND: dict[str, set[str]] = {
    EDITION_VENDOR: {
        "edition.vendor.tenants.read",
        "edition.vendor.resellers.read",
        "edition.vendor.resellers.create",
        "edition.vendor.resellers.manage",
        "edition.vendor.customers.read",
        "edition.vendor.customers.create",
        "edition.vendor.customers.manage",
        "edition.licenses.read",
        "edition.licenses.issue",
        "edition.licenses.revoke",
        "edition.support.read",
        "edition.support.reply",
        "edition.support.manage",
        "edition.support.attachment.read",
    },
    EDITION_RESELLER: {
        "edition.reseller.customers.read",
        "edition.reseller.customers.create",
        "edition.reseller.customers.manage",
        "edition.reseller.entitlements.read",
        "edition.reseller.entitlements.delegate",
        "edition.licenses.read",
        "edition.licenses.issue",
        "edition.licenses.revoke",
        "edition.support.read",
        "edition.support.create",
        "edition.support.reply",
        "edition.support.manage",
        "edition.support.attachment.read",
    },
    EDITION_CUSTOMER: {
        "edition.support.read",
        "edition.support.create",
        "edition.support.reply",
        "edition.support.attachment.read",
    },
}

# Method + route template suffix -> required API-key scope. Unmapped routes
# protected by an edition dependency fail closed for API keys, so new routes
# cannot accidentally inherit broad control-plane access.
EDITION_ROUTE_SCOPES: dict[tuple[str, str], str] = {
    ("GET", "/edition/vendor/tenants"): "edition.vendor.tenants.read",
    ("GET", "/edition/vendor/resellers"): "edition.vendor.resellers.read",
    ("POST", "/edition/vendor/resellers"): "edition.vendor.resellers.create",
    ("POST", "/edition/vendor/resellers/{reseller_id}/suspend"): "edition.vendor.resellers.manage",
    ("POST", "/edition/vendor/resellers/{reseller_id}/resume"): "edition.vendor.resellers.manage",
    ("POST", "/edition/vendor/resellers/{reseller_id}/deprovision"): "edition.vendor.resellers.manage",
    ("GET", "/edition/vendor/customers"): "edition.vendor.customers.read",
    ("POST", "/edition/vendor/customers"): "edition.vendor.customers.create",
    ("POST", "/edition/vendor/customers/{customer_id}/suspend"): "edition.vendor.customers.manage",
    ("POST", "/edition/vendor/customers/{customer_id}/resume"): "edition.vendor.customers.manage",
    ("POST", "/edition/vendor/customers/{customer_id}/deprovision"): "edition.vendor.customers.manage",
    ("GET", "/edition/reseller/customers"): "edition.reseller.customers.read",
    ("POST", "/edition/reseller/customers"): "edition.reseller.customers.create",
    ("POST", "/edition/reseller/customers/{customer_id}/suspend"): "edition.reseller.customers.manage",
    ("POST", "/edition/reseller/customers/{customer_id}/resume"): "edition.reseller.customers.manage",
    ("POST", "/edition/reseller/customers/{customer_id}/deprovision"): "edition.reseller.customers.manage",
    ("POST", "/edition/reseller/customers/{customer_id}/entitlements"): "edition.reseller.entitlements.delegate",
    ("GET", "/edition/vendor/support/escalations"): "edition.support.read",
    ("GET", "/edition/reseller/support/escalations"): "edition.support.read",
    ("GET", "/edition/reseller/support/escalations/sent"): "edition.support.read",
    ("PATCH", "/edition/vendor/support/escalations/{escalation_id}/status"): "edition.support.manage",
    ("PATCH", "/edition/reseller/support/escalations/{escalation_id}/status"): "edition.support.manage",
    ("GET", "/edition/support/escalations"): "edition.support.read",
    ("POST", "/edition/support/escalations"): "edition.support.create",
    ("POST", "/edition/reseller/support/escalations"): "edition.support.create",
    ("GET", "/edition/vendor/support/escalations/{escalation_id}/messages/{message_id}/attachments/{attachment_id}/download"): "edition.support.attachment.read",
    ("GET", "/edition/reseller/support/escalations/{escalation_id}/messages/{message_id}/attachments/{attachment_id}/download"): "edition.support.attachment.read",
    ("GET", "/edition/support/escalations/{escalation_id}/messages/{message_id}/attachments/{attachment_id}/download"): "edition.support.attachment.read",
    ("GET", "/edition/vendor/support/escalations/{escalation_id}/messages"): "edition.support.read",
    ("POST", "/edition/vendor/support/escalations/{escalation_id}/messages"): "edition.support.reply",
    ("GET", "/edition/reseller/support/escalations/{escalation_id}/messages"): "edition.support.read",
    ("POST", "/edition/reseller/support/escalations/{escalation_id}/messages"): "edition.support.reply",
    ("GET", "/edition/support/escalations/{escalation_id}/messages"): "edition.support.read",
    ("POST", "/edition/support/escalations/{escalation_id}/messages"): "edition.support.reply",
    ("GET", "/edition/customer/{customer_id}/entitlements"): "edition.reseller.entitlements.read",
    ("GET", "/edition/licenses/vendor"): "edition.licenses.read",
    ("GET", "/edition/licenses/reseller"): "edition.licenses.read",
    ("POST", "/edition/licenses/vendor/tenants/{tenant_id}"): "edition.licenses.issue",
    ("POST", "/edition/licenses/vendor/resellers/{reseller_id}"): "edition.licenses.issue",
    ("POST", "/edition/licenses/reseller/customers/{customer_id}"): "edition.licenses.issue",
    ("POST", "/edition/licenses/vendor/{license_id}/revoke"): "edition.licenses.revoke",
    ("POST", "/edition/licenses/reseller/{license_id}/revoke"): "edition.licenses.revoke",
}


def _enforce_api_key_scope(ctx: TenantContext, request: Request, kind: str) -> None:
    # api_key_id distinguishes API-key auth from bearer auth. Legacy API keys
    # may have scopes=NULL; never mistake those keys for bearer requests.
    if getattr(ctx, "api_key_id", None) is None:
        return
    api_key_scopes = getattr(ctx, "api_key_scopes", None)
    if api_key_scopes is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Legacy API keys without explicit scopes cannot access edition control-plane operations",
        )
    route = request.scope.get("route")
    route_path = getattr(route, "path", "")
    required_scope = next(
        (scope for (method, suffix), scope in EDITION_ROUTE_SCOPES.items()
         if request.method.upper() == method and route_path.endswith(suffix)),
        None,
    )
    if required_scope is None or required_scope not in EDITION_SCOPE_ALLOWLIST_BY_KIND[kind]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key is not authorized for this edition control-plane operation")
    if required_scope not in set(api_key_scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing API key scope: {required_scope}")


async def require_vendor_admin(ctx: CurrentContext, request: Request) -> TenantContext:
    """Authorize a vendor administrator and enforce API-key operation scope."""
    require_edition(ctx, EDITION_VENDOR)
    _enforce_api_key_scope(ctx, request, EDITION_VENDOR)
    return ctx


async def require_reseller_admin(ctx: CurrentContext, request: Request) -> TenantContext:
    require_edition(ctx, EDITION_RESELLER)
    _enforce_api_key_scope(ctx, request, EDITION_RESELLER)
    return ctx


async def require_customer_admin(ctx: CurrentContext, request: Request) -> TenantContext:
    require_edition(ctx, EDITION_CUSTOMER)
    _enforce_api_key_scope(ctx, request, EDITION_CUSTOMER)
    return ctx


async def _has_action_permission(ctx: TenantContext, db, permission_code: str) -> bool:
    actor_tenant_id = getattr(ctx, "actor_tenant_id", ctx.tenant_id)
    if any(permission.code == permission_code for role in ctx.user.roles if role.tenant_id == actor_tenant_id for permission in role.permissions):
        return True
    # API keys never inherit user-bound action grants.
    if getattr(ctx, "api_key_id", None) is not None or db is None:
        return False
    from app.services.tenant_action_grant_service import has_active_tenant_action_grant
    return await has_active_tenant_action_grant(db, user_id=ctx.user_id, tenant_id=actor_tenant_id, action_code=permission_code)


def require_vendor_permission(permission_code: str):
    """Require a tenant-local role permission or explicit user action grant."""
    async def checker(ctx: CurrentContext, request: Request, db: DbSession) -> TenantContext:
        if ctx.tenant.tenant_kind != EDITION_VENDOR:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor edition access required")
        _enforce_api_key_scope(ctx, request, EDITION_VENDOR)
        if not await _has_action_permission(ctx, db, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission_code}")
        return ctx
    return checker


def require_reseller_permission(permission_code: str):
    """Require a tenant-local role permission or explicit user action grant."""
    async def checker(ctx: CurrentContext, request: Request, db: DbSession) -> TenantContext:
        if ctx.tenant.tenant_kind != EDITION_RESELLER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reseller edition access required")
        _enforce_api_key_scope(ctx, request, EDITION_RESELLER)
        if not await _has_action_permission(ctx, db, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission_code}")
        return ctx
    return checker


require_vendor_tenant_read = require_vendor_permission("vendor.tenant.read")
require_vendor_reseller_read = require_vendor_permission("vendor.reseller.read")
require_vendor_reseller_create = require_vendor_permission("vendor.reseller.create")
require_vendor_reseller_manage = require_vendor_permission("vendor.reseller.manage")
require_vendor_customer_read = require_vendor_permission("vendor.customer.read")
require_vendor_customer_create = require_vendor_permission("vendor.customer.create")
require_vendor_customer_manage = require_vendor_permission("vendor.customer.manage")

require_reseller_customer_create = require_reseller_permission("reseller.customer.create")
require_reseller_customer_read = require_reseller_permission("reseller.customer.read")
require_reseller_customer_manage = require_reseller_permission("reseller.customer.manage")
require_reseller_entitlement_delegate = require_reseller_permission("reseller.entitlement.delegate")


VendorAdminContext = Annotated[TenantContext, Depends(require_vendor_admin)]
VendorTenantReadContext = Annotated[TenantContext, Depends(require_vendor_tenant_read)]
VendorResellerReadContext = Annotated[TenantContext, Depends(require_vendor_reseller_read)]
VendorResellerCreateContext = Annotated[TenantContext, Depends(require_vendor_reseller_create)]
VendorResellerManageContext = Annotated[TenantContext, Depends(require_vendor_reseller_manage)]
VendorCustomerReadContext = Annotated[TenantContext, Depends(require_vendor_customer_read)]
VendorCustomerCreateContext = Annotated[TenantContext, Depends(require_vendor_customer_create)]
VendorCustomerManageContext = Annotated[TenantContext, Depends(require_vendor_customer_manage)]
ResellerAdminContext = Annotated[TenantContext, Depends(require_reseller_admin)]
CustomerAdminContext = Annotated[TenantContext, Depends(require_customer_admin)]
ResellerCustomerCreateContext = Annotated[TenantContext, Depends(require_reseller_customer_create)]
ResellerCustomerReadContext = Annotated[TenantContext, Depends(require_reseller_customer_read)]
ResellerCustomerManageContext = Annotated[TenantContext, Depends(require_reseller_customer_manage)]
ResellerEntitlementDelegateContext = Annotated[TenantContext, Depends(require_reseller_entitlement_delegate)]

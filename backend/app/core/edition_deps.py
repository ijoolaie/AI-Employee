"""FastAPI dependencies for commercial edition boundaries."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.deps import CurrentContext, TenantContext
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


VendorAdminContext = Annotated[TenantContext, Depends(require_vendor_admin)]
ResellerAdminContext = Annotated[TenantContext, Depends(require_reseller_admin)]
CustomerAdminContext = Annotated[TenantContext, Depends(require_customer_admin)]

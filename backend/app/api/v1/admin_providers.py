"""Vendor-only platform provider health/read-only management surface."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.core.deps import TenantContext, get_current_context

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])


async def require_platform_admin(ctx: TenantContext = Depends(get_current_context)) -> TenantContext:
    if not ctx.user.is_platform_admin or ctx.tenant.tenant_kind != "vendor":
        raise HTTPException(status_code=403, detail="Vendor platform administrator access required")
    return ctx


PlatformAdminContext = Annotated[TenantContext, Depends(require_platform_admin)]


@router.get("")
async def provider_status(ctx: PlatformAdminContext):
    s = get_settings()
    providers = [
        {"name": "lm_studio", "category": "ai", "configured": bool(s.lm_studio_base_url), "secret_configured": bool(s.lm_studio_api_key)},
        {"name": "anthropic", "category": "ai", "configured": bool(s.anthropic_api_key), "secret_configured": bool(s.anthropic_api_key)},
        {"name": "stripe", "category": "billing", "configured": bool(s.stripe_secret_key), "secret_configured": bool(s.stripe_secret_key)},
        {"name": "shopify", "category": "commerce", "configured": bool(s.shopify_client_id and s.shopify_client_secret), "secret_configured": bool(s.shopify_client_secret)},
        {"name": "billing_webhook", "category": "webhook", "configured": bool(s.billing_webhook_secret), "secret_configured": bool(s.billing_webhook_secret)},
    ]
    return {"success": True, "data": {"providers": providers}}

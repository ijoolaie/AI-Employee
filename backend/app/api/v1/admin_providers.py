"""Platform provider health/read-only management surface.

This endpoint deliberately exposes configuration state, not secrets. Mutating
provider credentials remains an infrastructure/secret-management operation.
"""
from fastapi import APIRouter, HTTPException
from app.core.config import get_settings
from app.core.deps import TenantContext, get_current_context
from fastapi import Depends
from typing import Annotated

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])

async def require_platform_admin(ctx: TenantContext = Depends(get_current_context)) -> TenantContext:
    if not ctx.user.is_platform_admin:
        raise HTTPException(status_code=403, detail="Platform administrator access required")
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

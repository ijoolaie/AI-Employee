"""FastAPI dependencies for commercial edition boundaries."""

from typing import Annotated

from fastapi import Depends

from app.core.deps import CurrentContext, TenantContext
from app.services.edition_service import require_edition, EDITION_CUSTOMER, EDITION_RESELLER, EDITION_VENDOR


async def require_vendor_admin(ctx: CurrentContext) -> TenantContext:
    require_edition(ctx, EDITION_VENDOR)
    if not ctx.user.is_platform_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Vendor control-plane access required")
    return ctx


async def require_reseller_admin(ctx: CurrentContext) -> TenantContext:
    require_edition(ctx, EDITION_RESELLER)
    return ctx


async def require_customer_admin(ctx: CurrentContext) -> TenantContext:
    require_edition(ctx, EDITION_CUSTOMER)
    return ctx


VendorAdminContext = Annotated[TenantContext, Depends(require_vendor_admin)]
ResellerAdminContext = Annotated[TenantContext, Depends(require_reseller_admin)]
CustomerAdminContext = Annotated[TenantContext, Depends(require_customer_admin)]

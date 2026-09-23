"""Read-only first-party AI Company workforce role catalog."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import TenantContext, require_permission
from app.services.ai_workforce_roles import list_workforce_roles

router = APIRouter(prefix="/ai-workforce-roles", tags=["ai-workforce-roles"])


@router.get("")
async def get_ai_workforce_roles(
    _ctx: TenantContext = Depends(require_permission("agent_workforce.read")),
) -> list[dict]:
    """Return the governed first-party role catalog without provisioning anything."""
    return list_workforce_roles()
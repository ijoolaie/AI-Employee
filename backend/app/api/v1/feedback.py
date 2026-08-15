"""Feedback endpoints — Phase 3 "Validation" support (03_Roadmap_v1.1 §6).

Lets a tenant user record feedback about a Run or the product in general.
Tenant-scoped through the standard TenantContext exactly like every other
route in this API; feedback.create/feedback.read are ordinary RBAC
permissions (seeded onto the tenant Admin role, see auth_service.py).
"""

from fastapi import APIRouter, status

from app.core.deps import DbSession, FeedbackCreateContext, FeedbackReadContext
from app.schemas.common import APIResponse
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services import feedback_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=APIResponse[FeedbackResponse], status_code=status.HTTP_201_CREATED)
async def submit_feedback(payload: FeedbackCreate, ctx: FeedbackCreateContext, db: DbSession):
    feedback = await feedback_service.create_feedback(
        db,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        rating=payload.rating,
        comment=payload.comment,
        run_id=payload.run_id,
        employee_id=payload.employee_id,
        category=payload.category,
    )
    return APIResponse(success=True, data=FeedbackResponse.model_validate(feedback))


@router.get("", response_model=APIResponse[list[FeedbackResponse]])
async def list_feedback(ctx: FeedbackReadContext, db: DbSession):
    items = await feedback_service.list_feedback(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=[FeedbackResponse.model_validate(f) for f in items])

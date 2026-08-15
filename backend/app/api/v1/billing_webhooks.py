"""Public Stripe webhook receiver (Phase 6).

Deliberately a separate router from app/api/v1/billing.py: this endpoint
is unauthenticated by user credentials (Stripe cannot supply a Bearer
token) and instead relies entirely on Stripe's own webhook signature
scheme (verified inside stripe_service.verify_and_parse_webhook). It is
mounted under /api/v1/webhooks/... so it inherits the existing webhook
payload-size limit and rate limiting already applied to that path prefix
in app/core/middleware.py — the same treatment
/api/v1/webhooks/workflows/{trigger_id} gets.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.core.deps import DbSession
from app.core.exceptions import ValidationAppError
from app.services import stripe_service

router = APIRouter(tags=["billing-webhooks"])


@router.post("/webhooks/billing/stripe", status_code=status.HTTP_200_OK)
async def receive_stripe_webhook(
    request: Request,
    db: DbSession,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    settings = get_settings()
    if not settings.stripe_enabled:
        # Fail closed: an unconfigured deployment should not silently
        # accept (and ignore) webhook calls that look successful.
        raise HTTPException(status_code=503, detail="Stripe is not configured on this deployment")

    body = await request.body()
    if len(body) > settings.webhook_max_payload_bytes:
        raise HTTPException(status_code=413, detail="Webhook payload too large")

    try:
        event = stripe_service.verify_and_parse_webhook(body, stripe_signature)
    except ValidationAppError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = await stripe_service.apply_webhook_event(db, event)
    await db.commit()
    return {"success": True, "data": result}

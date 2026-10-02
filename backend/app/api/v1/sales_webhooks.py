"""Provider-backed Sales Employee inbound response webhook."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.core.deps import DbSession
from app.core.exceptions import ValidationAppError
from app.services import workforce_sales_engagement
from app.services import workforce_sales_inbound_provider

router = APIRouter(prefix="/webhooks/sales", tags=["sales-webhooks"])


@router.post("/outreach/{tenant_id}", status_code=status.HTTP_202_ACCEPTED)
async def receive_sales_outreach_response(
    tenant_id: uuid.UUID,
    request: Request,
    db: DbSession,
    x_sales_event_id: str | None = Header(default=None),
    x_sales_provider_message_id: str | None = Header(default=None),
    x_sales_signature: str | None = Header(default=None),
):
    """Accept one authenticated provider response and attribute it to delivery.

    The public payload carries only response content. Deal/outbox/tool-call
    correlation is always derived from the tenant's immutable delivery event.
    """
    provider = (get_settings().sales_inbound_provider_name or "none").strip().lower()
    if provider not in {"contract-test", "generic-webhook"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sales inbound response provider is not configured",
        )

    body = await request.body()
    try:
        inbound = workforce_sales_inbound_provider.parse_and_verify(
            tenant_id=tenant_id,
            body=body,
            event_id=x_sales_event_id,
            provider_message_id=x_sales_provider_message_id,
            signature=x_sales_signature,
        )
    except ValidationAppError as exc:
        message = str(exc)
        if "signature" in message.lower():
            code = status.HTTP_401_UNAUTHORIZED
        elif "payload" in message.lower() or "response_text" in message.lower() or "message id" in message.lower():
            code = status.HTTP_400_BAD_REQUEST
        else:
            code = status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(status_code=code, detail=message) from exc

    try:
        event = await workforce_sales_engagement.ingest_outreach_response(
            db,
            tenant_id=tenant_id,
            event_key=inbound.event_key,
            provider_message_id=inbound.provider_message_id,
            response_text=inbound.response_text,
            source=f"provider:{inbound.provider}",
        )
    except ValueError as exc:
        message = str(exc)
        if "correlate" in message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc

    return {
        "success": True,
        "event_id": str(event.id),
        "event_key": inbound.event_key,
        "duplicate": bool((event.metadata_ or {}).get("event_key") == inbound.event_key),
        "provider": inbound.provider,
        "event_type": "outreach_response",
    }

"""Public ZarinPal payment callback and server-side verification boundary."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DbSession
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.business_deal import BusinessDeal
from app.services import stripe_service, zarinpal_service

router = APIRouter(tags=["billing-webhooks"])


@router.get("/webhooks/billing/zarinpal", status_code=status.HTTP_200_OK)
async def receive_zarinpal_callback(
    request: Request,
    db: DbSession,
):
    settings = get_settings()
    if not settings.zarinpal_merchant_id:
        raise HTTPException(status_code=503, detail="ZarinPal is not configured on this deployment")

    deal_ref = request.query_params.get("deal_id")
    authority = request.query_params.get("Authority")
    provider_status = request.query_params.get("Status")
    if not deal_ref or not authority:
        raise HTTPException(status_code=400, detail="ZarinPal callback is missing deal_id or Authority")
    try:
        deal_id = uuid.UUID(deal_ref)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid deal_id") from exc

    deal = (
        await db.execute(
            select(BusinessDeal).where(BusinessDeal.id == deal_id).with_for_update()
        )
    ).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail="Sales deal not found")

    metadata = dict(deal.metadata_ or {})
    if metadata.get("payment_provider") != "zarinpal":
        raise HTTPException(status_code=409, detail="Sales deal is not bound to ZarinPal")

    stored_authority = metadata.get("payment_provider_authority")
    attempt_state = metadata.get("payment_attempt_state")
    if stored_authority and stored_authority != authority:
        raise HTTPException(status_code=409, detail="ZarinPal authority does not match the governed checkout")

    if provider_status != "OK":
        if attempt_state == "pending" and not stored_authority:
            metadata["payment_attempt_state"] = "cancelled"
            deal.metadata_ = metadata
            await db.commit()
        return {"success": False, "status": "cancelled", "deal_id": str(deal.id)}

    # The callback can arrive after provider acceptance but before the checkout
    # creator persists the authority. Verify the callback authority against the
    # governed amount, then bind it locally; never create another checkout.
    if not stored_authority:
        if attempt_state != "pending":
            raise HTTPException(status_code=409, detail="ZarinPal checkout authority is not bound to a pending attempt")
        metadata["payment_provider_authority"] = authority
        metadata["payment_attempt_state"] = "accepted"
        metadata["payment_amount"] = float(deal.amount)
        metadata["payment_currency"] = deal.currency.upper()
        deal.metadata_ = metadata
        await db.flush()

    verification = await zarinpal_service.verify_payment(
        authority=authority,
        amount=deal.amount,
        currency=deal.currency,
    )
    ref_id = verification.get("ref_id")
    if not ref_id:
        raise HTTPException(status_code=502, detail="ZarinPal verification returned no reference id")

    try:
        tenant_id, order_id = await stripe_service.apply_verified_sales_payment(
            db,
            provider="zarinpal",
            provider_event_id=str(ref_id),
            data={
                "id": str(ref_id),
                "amount_received": zarinpal_service._rial_amount(deal.amount, deal.currency),
                "currency": "IRR",
                "metadata": {
                    "tenant_id": str(deal.tenant_id),
                    "sales_deal_id": str(deal.id),
                },
            },
        )
        await db.commit()
    except (ValidationAppError, ConflictError, NotFoundError) as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "success": True,
        "status": "paid",
        "provider": "zarinpal",
        "deal_id": str(deal.id),
        "tenant_id": str(tenant_id),
        "order_id": order_id,
        "reference_id": str(ref_id),
    }

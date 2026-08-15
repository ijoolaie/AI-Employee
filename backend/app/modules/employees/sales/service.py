"""Sales Employee domain service (Phase 9).

Lightweight CRM: deals/opportunities, pipeline summary, simple forecast.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.business_deal import BusinessDeal
from app.services import audit_service

ALLOWED_STAGES = frozenset(
    {"lead", "qualified", "proposal", "negotiation", "won", "lost"}
)

DEFAULT_PROBABILITY = {
    "lead": 10,
    "qualified": 25,
    "proposal": 50,
    "negotiation": 70,
    "won": 100,
    "lost": 0,
}


def _money(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"))


async def create_deal(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    title: str,
    customer_name: str,
    amount: float | Decimal = 0,
    currency: str = "IRR",
    stage: str = "lead",
    probability: int | None = None,
    customer_email: str | None = None,
    expected_close_date: date | None = None,
    owner_name: str | None = None,
    notes: str | None = None,
    source: str | None = None,
    order_id: str | None = None,
) -> BusinessDeal:
    if not title or not str(title).strip():
        raise ValidationAppError("title is required")
    if not customer_name or not str(customer_name).strip():
        raise ValidationAppError("customer_name is required")
    stage = (stage or "lead").lower()
    if stage not in ALLOWED_STAGES:
        raise ValidationAppError(f"stage must be one of {sorted(ALLOWED_STAGES)}")

    amt = _money(Decimal(str(amount)))
    if amt < 0:
        raise ValidationAppError("amount must be >= 0")

    prob = probability if probability is not None else DEFAULT_PROBABILITY[stage]
    if prob < 0 or prob > 100:
        raise ValidationAppError("probability must be 0-100")

    order_uuid = None
    if order_id:
        try:
            order_uuid = uuid.UUID(str(order_id))
        except ValueError as exc:
            raise ValidationAppError("order_id must be a valid UUID") from exc

    deal = BusinessDeal(
        tenant_id=tenant_id,
        title=str(title).strip()[:255],
        customer_name=str(customer_name).strip()[:255],
        customer_email=customer_email,
        stage=stage,
        amount=amt,
        currency=(currency or "IRR").upper()[:8],
        probability=int(prob),
        expected_close_date=expected_close_date,
        owner_name=owner_name,
        notes=notes,
        source=source,
        order_id=order_uuid,
        created_by=actor_id,
        metadata_={},
    )
    db.add(deal)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="deal.created",
        resource_type="business_deal",
        resource_id=str(deal.id),
        metadata={"title": deal.title, "stage": deal.stage, "amount": float(deal.amount)},
    )
    return deal


async def update_stage(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    deal_id: str,
    stage: str,
    probability: int | None = None,
) -> BusinessDeal:
    stage = stage.lower()
    if stage not in ALLOWED_STAGES:
        raise ValidationAppError(f"stage must be one of {sorted(ALLOWED_STAGES)}")
    deal = await get_deal(db, tenant_id=tenant_id, deal_id=deal_id)
    deal.stage = stage
    if probability is not None:
        if probability < 0 or probability > 100:
            raise ValidationAppError("probability must be 0-100")
        deal.probability = probability
    else:
        deal.probability = DEFAULT_PROBABILITY[stage]
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="deal.stage_updated",
        resource_type="business_deal",
        resource_id=str(deal.id),
        metadata={"stage": stage, "probability": deal.probability},
    )
    return deal


async def get_deal(db: AsyncSession, *, tenant_id: uuid.UUID, deal_id: str) -> BusinessDeal:
    try:
        did = uuid.UUID(str(deal_id))
    except ValueError as exc:
        raise ValidationAppError("deal_id must be a valid UUID") from exc
    result = await db.execute(
        select(BusinessDeal).where(
            BusinessDeal.id == did,
            BusinessDeal.tenant_id == tenant_id,
        )
    )
    deal = result.scalar_one_or_none()
    if deal is None:
        raise NotFoundError("Deal not found")
    return deal


async def list_deals(
    db: AsyncSession, *, tenant_id: uuid.UUID, stage: str | None = None
) -> list[BusinessDeal]:
    stmt = select(BusinessDeal).where(BusinessDeal.tenant_id == tenant_id)
    if stage:
        stage = stage.lower()
        if stage not in ALLOWED_STAGES:
            raise ValidationAppError(f"stage must be one of {sorted(ALLOWED_STAGES)}")
        stmt = stmt.where(BusinessDeal.stage == stage)
    stmt = stmt.order_by(BusinessDeal.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def pipeline_summary(db: AsyncSession, *, tenant_id: uuid.UUID) -> dict[str, Any]:
    rows = await list_deals(db, tenant_id=tenant_id)
    counts: dict[str, int] = {}
    amounts: dict[str, float] = {}
    weighted = 0.0
    won = 0.0
    lost = 0.0
    open_n = 0
    currency = "IRR"
    for d in rows:
        currency = d.currency or currency
        counts[d.stage] = counts.get(d.stage, 0) + 1
        amounts[d.stage] = amounts.get(d.stage, 0.0) + float(d.amount)
        if d.stage == "won":
            won += float(d.amount)
        elif d.stage == "lost":
            lost += float(d.amount)
        else:
            open_n += 1
            weighted += float(d.amount) * (d.probability / 100.0)
    return {
        "counts_by_stage": counts,
        "amount_by_stage": amounts,
        "weighted_pipeline": round(weighted, 2),
        "won_amount": round(won, 2),
        "lost_amount": round(lost, 2),
        "open_deals": open_n,
        "total_deals": len(rows),
        "currency": currency,
    }


async def simple_forecast(
    db: AsyncSession, *, tenant_id: uuid.UUID, horizon_days: int = 30
) -> dict[str, Any]:
    """Simple forecast: sum of open deals expected to close within horizon,
    weighted by probability. Deliberately auditable (not an opaque ML model).
    """
    if horizon_days < 1 or horizon_days > 365:
        raise ValidationAppError("horizon_days must be 1-365")
    rows = await list_deals(db, tenant_id=tenant_id)
    cutoff = date.today() + timedelta(days=horizon_days)
    expected = 0.0
    considered = 0
    currency = "IRR"
    for d in rows:
        if d.stage in ("won", "lost"):
            continue
        currency = d.currency or currency
        close = d.expected_close_date or (date.today() + timedelta(days=14))
        if close <= cutoff:
            expected += float(d.amount) * (d.probability / 100.0)
            considered += 1
    return {
        "method": "weighted_open_deals_by_close_date",
        "horizon_days": horizon_days,
        "expected_revenue": round(expected, 2),
        "currency": currency,
        "assumptions": {
            "deals_considered": considered,
            "missing_close_date_default_days": 14,
            "note": "Probability-weighted sum of open deals with expected_close_date within horizon.",
        },
    }

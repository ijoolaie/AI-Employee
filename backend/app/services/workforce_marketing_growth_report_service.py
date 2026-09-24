"""Tenant-safe commercial growth reporting for the AI Marketing Manager."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_deal import BusinessDeal
from app.models.business_order import BusinessOrder


async def prepare_growth_report(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    window_days: int = 30,
) -> dict[str, Any]:
    """Prepare an auditable growth report from tenant-owned sales/order data.

    This is intentionally read-only. It does not infer campaign performance and
    does not mutate commercial data. Campaign-specific capabilities remain
    unbound until a real campaign domain exists.
    """
    if window_days < 1 or window_days > 365:
        raise ValueError("window_days must be 1-365")

    start_date = date.today() - timedelta(days=window_days - 1)

    orders_result = await db.execute(
        select(BusinessOrder).where(
            BusinessOrder.tenant_id == tenant_id,
            BusinessOrder.order_date >= start_date,
        )
    )
    orders = list(orders_result.scalars().all())

    deals_result = await db.execute(
        select(BusinessDeal).where(
            BusinessDeal.tenant_id == tenant_id,
            BusinessDeal.created_at >= start_date,
        )
    )
    deals = list(deals_result.scalars().all())

    order_revenue = sum(float(order.total) for order in orders)
    delivered_revenue = sum(
        float(order.total) for order in orders if order.status == "delivered"
    )
    cancelled_revenue = sum(
        float(order.total) for order in orders if order.status == "cancelled"
    )

    won_amount = sum(float(deal.amount) for deal in deals if deal.stage == "won")
    open_deals = [deal for deal in deals if deal.stage not in {"won", "lost"}]
    weighted_pipeline = sum(
        float(deal.amount) * (deal.probability / 100.0) for deal in open_deals
    )
    closed_deals = [deal for deal in deals if deal.stage in {"won", "lost"}]
    win_rate = (
        len([deal for deal in closed_deals if deal.stage == "won"]) / len(closed_deals)
        if closed_deals
        else None
    )

    currencies = {
        str(value)
        for value in [
            *(order.currency for order in orders),
            *(deal.currency for deal in deals),
        ]
        if value
    }

    return {
        "window_days": window_days,
        "start_date": start_date.isoformat(),
        "currency_scope": sorted(currencies),
        "orders": {
            "count": len(orders),
            "revenue": round(order_revenue, 2),
            "delivered_revenue": round(delivered_revenue, 2),
            "cancelled_revenue": round(cancelled_revenue, 2),
        },
        "sales_pipeline": {
            "deal_count": len(deals),
            "won_amount": round(won_amount, 2),
            "open_deals": len(open_deals),
            "weighted_pipeline": round(weighted_pipeline, 2),
            "closed_deals": len(closed_deals),
            "win_rate": round(win_rate, 4) if win_rate is not None else None,
        },
        "scope_note": (
            "Commercial growth report from tenant-owned orders and sales deals. "
            "It is not campaign-attribution or ad-performance analysis."
        ),
    }

"""Verified marketplace financial allocation without external payout."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.skill_marketplace_purchase import (
    SkillMarketplacePurchase,
    SkillMarketplacePurchaseStatus,
)
from app.models.skill_marketplace_settlement import (
    SkillMarketplacePayoutStatus,
    SkillMarketplaceSettlement,
    SkillMarketplaceSettlementStatus,
)
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.services import audit_service


def _calculate_split(gross_amount: Decimal, fee_bps: int) -> tuple[Decimal, Decimal]:
    if gross_amount <= 0:
        raise ValidationAppError("marketplace settlement gross amount must be positive")
    if fee_bps < 0 or fee_bps > 10_000:
        raise ValidationAppError("marketplace platform fee bps must be between 0 and 10000")
    fee = (gross_amount * Decimal(fee_bps) / Decimal(10_000)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    seller_net = gross_amount - fee
    if seller_net < 0:
        raise ValidationAppError("marketplace settlement seller net cannot be negative")
    return fee, seller_net


async def record_verified_payment_allocation(
    db: AsyncSession,
    *,
    purchase_id: uuid.UUID,
    revenue_event_id: uuid.UUID,
    buyer_tenant_id: uuid.UUID,
    provider: str,
    provider_event_id: str,
    verified_at: datetime | None = None,
) -> SkillMarketplaceSettlement:
    settings = get_settings()
    if not settings.skill_marketplace_settlement_enabled:
        raise ValidationAppError(
            "marketplace financial allocation is not enabled on this deployment"
        )

    purchase = (
        await db.execute(
            select(SkillMarketplacePurchase).where(
                SkillMarketplacePurchase.id == purchase_id,
                SkillMarketplacePurchase.buyer_tenant_id == buyer_tenant_id,
                SkillMarketplacePurchase.status == SkillMarketplacePurchaseStatus.PAID,
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if purchase is None:
        raise NotFoundError("paid marketplace purchase not found")

    revenue = (
        await db.execute(
            select(WorkforceRevenueEvent).where(
                WorkforceRevenueEvent.id == revenue_event_id,
                WorkforceRevenueEvent.tenant_id == buyer_tenant_id,
                WorkforceRevenueEvent.provider == provider,
                WorkforceRevenueEvent.provider_event_id == provider_event_id,
            )
        )
    ).scalar_one_or_none()
    if revenue is None:
        raise NotFoundError("verified marketplace revenue event not found")

    existing = (
        await db.execute(
            select(SkillMarketplaceSettlement).where(
                SkillMarketplaceSettlement.purchase_id == purchase_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if (
            existing.provider != provider
            or existing.provider_event_id != provider_event_id
            or existing.revenue_event_id != revenue_event_id
        ):
            raise ConflictError("marketplace settlement replay does not match the original allocation")
        return existing

    fee_bps = int(settings.skill_marketplace_platform_fee_bps)
    fee, seller_net = _calculate_split(purchase.amount, fee_bps)

    settlement = SkillMarketplaceSettlement(
        purchase_id=purchase.id,
        revenue_event_id=revenue.id,
        buyer_tenant_id=purchase.buyer_tenant_id,
        seller_tenant_id=purchase.seller_tenant_id,
        provider=provider,
        provider_event_id=provider_event_id,
        gross_amount=purchase.amount,
        platform_fee_bps=fee_bps,
        platform_fee_amount=fee,
        seller_net_amount=seller_net,
        currency=purchase.currency,
        status=SkillMarketplaceSettlementStatus.RECORDED,
        payout_status=SkillMarketplacePayoutStatus.NOT_EXECUTED,
        metadata_={
            "source": "skill_marketplace",
            "tax_treatment": "not_calculated",
            "seller_payout": "not_executed",
            "platform_commission_accounting": True,
        },
        verified_at=verified_at or datetime.now(timezone.utc),
    )
    db.add(settlement)
    await db.flush()

    await audit_service.record(
        db,
        tenant_id=buyer_tenant_id,
        actor_id=None,
        action="skill_marketplace_settlement.recorded",
        resource_type="skill_marketplace_settlement",
        resource_id=str(settlement.id),
        metadata={
            "purchase_id": str(purchase.id),
            "revenue_event_id": str(revenue.id),
            "buyer_tenant_id": str(purchase.buyer_tenant_id),
            "seller_tenant_id": str(purchase.seller_tenant_id),
            "gross_amount": str(purchase.amount),
            "platform_fee_bps": fee_bps,
            "platform_fee_amount": str(fee),
            "seller_net_amount": str(seller_net),
            "currency": purchase.currency,
            "seller_payout": "not_executed",
            "tax_treatment": "not_calculated",
            "execution_authority_changed": False,
        },
    )
    await db.flush()
    return settlement

"""Read-only marketplace financial outcome reporting from verified settlements."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.skill_marketplace_payout_proposal import SkillMarketplacePayoutProposal
from app.models.skill_marketplace_purchase import SkillMarketplacePurchase
from app.models.skill_marketplace_settlement import SkillMarketplaceSettlement, SkillMarketplaceSettlementStatus


async def marketplace_financial_summary(
    db: AsyncSession,
    *,
    platform_admin_tenant_id: uuid.UUID,
    seller_tenant_id: uuid.UUID | None = None,
) -> dict:
    """Aggregate only recorded marketplace settlements; never mutates financial state."""
    stmt = (
        select(
            SkillMarketplaceSettlement.currency,
            func.count(SkillMarketplaceSettlement.id),
            func.sum(SkillMarketplaceSettlement.gross_amount),
            func.sum(SkillMarketplaceSettlement.platform_fee_amount),
            func.sum(SkillMarketplaceSettlement.seller_net_amount),
        )
        .where(
            SkillMarketplaceSettlement.status == SkillMarketplaceSettlementStatus.RECORDED,
        )
        .group_by(SkillMarketplaceSettlement.currency)
        .order_by(SkillMarketplaceSettlement.currency)
    )
    if seller_tenant_id is not None:
        stmt = stmt.where(SkillMarketplaceSettlement.seller_tenant_id == seller_tenant_id)

    rows = (await db.execute(stmt)).all()
    by_currency = {}
    total_settlements = 0
    for currency, count, gross, fee, seller_net in rows:
        total_settlements += int(count)
        by_currency[currency] = {
            "settlement_count": int(count),
            "gross_amount": str(Decimal(gross or 0)),
            "platform_fee_amount": str(Decimal(fee or 0)),
            "seller_net_amount": str(Decimal(seller_net or 0)),
        }

    purchase_stmt = select(func.count(SkillMarketplacePurchase.id)).where(
        SkillMarketplacePurchase.status == "paid",
    )
    if seller_tenant_id is not None:
        purchase_stmt = purchase_stmt.where(
            SkillMarketplacePurchase.seller_tenant_id == seller_tenant_id
        )
    paid_purchases = int((await db.execute(purchase_stmt)).scalar_one() or 0)

    proposal_stmt = select(func.count(SkillMarketplacePayoutProposal.id)).where(
        SkillMarketplacePayoutProposal.seller_tenant_id == seller_tenant_id
        if seller_tenant_id is not None
        else SkillMarketplacePayoutProposal.platform_admin_tenant_id == platform_admin_tenant_id
    )
    payout_proposals = int((await db.execute(proposal_stmt)).scalar_one() or 0)

    return {
        "verified_settlement_count": total_settlements,
        "verified_paid_purchase_count": paid_purchases,
        "payout_proposal_count": payout_proposals,
        "by_currency": by_currency,
        "evidence_basis": "recorded_skill_marketplace_settlements_only",
        "external_customer_revenue_verified": False,
        "external_seller_payout_verified": False,
        "execution_authority_changed": False,
    }

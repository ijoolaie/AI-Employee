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
from app.models.business_order import BusinessOrder
from app.models.employee import Employee
from app.models.product import Product
from app.models.skill_package import SkillPackage, SkillPackageStatus
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
    cosmetic_purchase: dict[str, Any] | None = None,
    skill_purchase: dict[str, Any] | None = None,
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

    cosmetic_contract = None
    if cosmetic_purchase is not None:
        required = {"employee_id", "product_id", "cosmetic_type", "cosmetic_value"}
        if set(cosmetic_purchase) != required:
            raise ValidationAppError("cosmetic_purchase must contain exactly employee_id, product_id, cosmetic_type, cosmetic_value")
        try:
            cosmetic_employee_id = uuid.UUID(str(cosmetic_purchase["employee_id"]))
            cosmetic_product_id = uuid.UUID(str(cosmetic_purchase["product_id"]))
        except (TypeError, ValueError) as exc:
            raise ValidationAppError("cosmetic_purchase employee_id/product_id must be valid UUIDs") from exc
        employee = (await db.execute(select(Employee).where(
            Employee.id == cosmetic_employee_id,
            Employee.tenant_id == tenant_id,
        ))).scalar_one_or_none()
        if employee is None:
            raise NotFoundError("Cosmetic purchase employee not found")
        product = (await db.execute(select(Product).where(
            Product.id == cosmetic_product_id,
            Product.tenant_id == tenant_id,
        ))).scalar_one_or_none()
        if product is None:
            raise NotFoundError("Cosmetic purchase product not found")
        from app.services.cosmetic_entitlement_service import _validate_product_contract
        cosmetic_type = str(cosmetic_purchase["cosmetic_type"])
        cosmetic_value = str(cosmetic_purchase["cosmetic_value"])
        _validate_product_contract(product, cosmetic_type, cosmetic_value)
        if (product.currency or "").upper() != (currency or "").upper() or _money(product.price) != amt:
            raise ValidationAppError("Cosmetic purchase amount/currency must match the catalog product")
        cosmetic_contract = {
            "employee_id": str(cosmetic_employee_id),
            "product_id": str(cosmetic_product_id),
            "cosmetic_type": cosmetic_type,
            "cosmetic_value": cosmetic_value,
        }

    skill_contract = None
    if skill_purchase is not None:
        required = {"employee_id", "product_id", "skill_package_id"}
        if set(skill_purchase) != required:
            raise ValidationAppError("skill_purchase must contain exactly employee_id, product_id, skill_package_id")
        try:
            skill_employee_id = uuid.UUID(str(skill_purchase["employee_id"]))
            skill_product_id = uuid.UUID(str(skill_purchase["product_id"]))
            skill_package_id = uuid.UUID(str(skill_purchase["skill_package_id"]))
        except (TypeError, ValueError) as exc:
            raise ValidationAppError("skill_purchase employee_id/product_id/skill_package_id must be valid UUIDs") from exc
        employee = (await db.execute(select(Employee).where(
            Employee.id == skill_employee_id,
            Employee.tenant_id == tenant_id,
        ))).scalar_one_or_none()
        if employee is None:
            raise NotFoundError("Skill purchase employee not found")
        product = (await db.execute(select(Product).where(
            Product.id == skill_product_id,
            Product.tenant_id == tenant_id,
        ))).scalar_one_or_none()
        if product is None:
            raise NotFoundError("Skill purchase product not found")
        package = (await db.execute(select(SkillPackage).where(
            SkillPackage.id == skill_package_id,
            SkillPackage.tenant_id == tenant_id,
            SkillPackage.status == SkillPackageStatus.PUBLISHED,
        ))).scalar_one_or_none()
        if package is None:
            raise NotFoundError("Skill purchase package not found or unpublished")
        if package.product_id != product.id or product.category != "employee_skill" or not product.is_active:
            raise ValidationAppError("Skill purchase product does not match an active employee skill package")
        attributes = product.attributes or {}
        if attributes.get("skill_package_slug") != package.slug:
            raise ValidationAppError("Skill purchase product does not match package slug")
        try:
            product_version = int(attributes.get("skill_package_version", -1))
        except (TypeError, ValueError):
            raise ValidationAppError("Skill purchase product version is invalid") from None
        if product_version != package.version:
            raise ValidationAppError("Skill purchase product does not match package version")
        if (product.currency or "").upper() != (currency or "").upper() or _money(product.price) != amt:
            raise ValidationAppError("Skill purchase amount/currency must match the catalog product")
        skill_contract = {
            "employee_id": str(skill_employee_id),
            "product_id": str(skill_product_id),
            "skill_package_id": str(skill_package_id),
        }

    order_uuid = None
    if order_id:
        try:
            order_uuid = uuid.UUID(str(order_id))
        except ValueError as exc:
            raise ValidationAppError("order_id must be a valid UUID") from exc
        order = (await db.execute(select(BusinessOrder).where(
            BusinessOrder.id == order_uuid,
            BusinessOrder.tenant_id == tenant_id,
        ))).scalar_one_or_none()
        if order is None:
            raise NotFoundError("Order not found")

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
        metadata_={
            **({"cosmetic_purchase": cosmetic_contract} if cosmetic_contract else {}),
            **({"skill_purchase": skill_contract} if skill_contract else {}),
        },
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
    deal = await get_deal(db, tenant_id=tenant_id, deal_id=deal_id, for_update=True)
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


async def get_deal(db: AsyncSession, *, tenant_id: uuid.UUID, deal_id: str, for_update: bool = False) -> BusinessDeal:
    try:
        did = uuid.UUID(str(deal_id))
    except ValueError as exc:
        raise ValidationAppError("deal_id must be a valid UUID") from exc
    stmt = select(BusinessDeal).where(
        BusinessDeal.id == did,
        BusinessDeal.tenant_id == tenant_id,
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
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

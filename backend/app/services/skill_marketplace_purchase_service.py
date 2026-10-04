"""Cross-tenant Skill Marketplace purchase and verified-payment boundary."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.business_deal import BusinessDeal
from app.models.employee import Employee
from app.models.product import Product
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.models.skill_marketplace_purchase import SkillMarketplacePurchase, SkillMarketplacePurchaseStatus
from app.models.skill_package import SkillPackage, SkillPackageStatus
from app.models.tenant import Tenant
from app.services.workforce_sales_payment_provider import create_sales_checkout_session
from app.services import audit_service


async def prepare_purchase(
    db: AsyncSession,
    *,
    buyer_tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    publication_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    customer_email: str | None,
    idempotency_key: str,
) -> tuple[SkillMarketplacePurchase, BusinessDeal, bool]:
    key = idempotency_key.strip()
    if not key or len(key) > 255:
        raise ValidationAppError("skill marketplace purchase idempotency key is invalid")

    await db.execute(select(Tenant).where(Tenant.id == buyer_tenant_id).with_for_update())

    existing = (
        await db.execute(
            select(SkillMarketplacePurchase).where(
                SkillMarketplacePurchase.buyer_tenant_id == buyer_tenant_id,
                SkillMarketplacePurchase.idempotency_key == key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        deal = (
            await db.execute(
                select(BusinessDeal).where(
                    BusinessDeal.id == existing.business_deal_id,
                    BusinessDeal.tenant_id == buyer_tenant_id,
                )
            )
        ).scalar_one()
        return existing, deal, True

    employee = (
        await db.execute(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.tenant_id == buyer_tenant_id,
                Employee.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if employee is None:
        raise NotFoundError("buyer employee not found in tenant")

    publication = (
        await db.execute(
            select(SkillMarketplacePublication).where(
                SkillMarketplacePublication.id == publication_id,
                SkillMarketplacePublication.visibility == "public",
            )
        )
    ).scalar_one_or_none()
    if publication is None:
        raise NotFoundError("public skill marketplace publication not found")
    if publication.owner_tenant_id == buyer_tenant_id:
        raise ConflictError("a tenant cannot purchase its own marketplace publication")

    package = (
        await db.execute(
            select(SkillPackage).where(
                SkillPackage.id == publication.skill_package_id,
                SkillPackage.tenant_id == publication.owner_tenant_id,
                SkillPackage.status == SkillPackageStatus.PUBLISHED,
            )
        )
    ).scalar_one_or_none()
    if package is None:
        raise NotFoundError("published marketplace skill package not found")
    if package.product_id is None:
        raise ConflictError("marketplace purchase requires a paid skill product")

    product = (
        await db.execute(
            select(Product).where(
                Product.id == package.product_id,
                Product.tenant_id == publication.owner_tenant_id,
                Product.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if product is None:
        raise NotFoundError("marketplace skill product not found or inactive")

    from app.services.skill_marketplace_service import _validate_product_contract
    _validate_product_contract(product, package)

    amount = Decimal(str(product.price))
    currency = (product.currency or "").upper()
    if amount <= 0:
        raise ValidationAppError("marketplace skill product price must be positive")
    if len(currency) != 3 or not currency.isalpha():
        raise ValidationAppError("marketplace skill product currency is invalid")

    deal = BusinessDeal(
        tenant_id=buyer_tenant_id,
        title=f"Skill Marketplace Purchase: {publication.title}"[:255],
        customer_name=employee.name[:255],
        customer_email=customer_email,
        stage="proposal",
        amount=amount,
        currency=currency,
        probability=50,
        source="skill_marketplace",
        created_by=actor_id,
        metadata_={
            "skill_purchase": {
                "employee_id": str(employee_id),
                "product_id": str(product.id),
                "skill_package_id": str(package.id),
            },
            "skill_marketplace_purchase": {
                "buyer_tenant_id": str(buyer_tenant_id),
                "seller_tenant_id": str(publication.owner_tenant_id),
                "publication_id": str(publication.id),
                "employee_id": str(employee_id),
                "product_id": str(product.id),
                "skill_package_id": str(package.id),
                "skill_package_slug": package.slug,
                "skill_package_version": package.version,
                "idempotency_key": key,
            },
        },
    )
    db.add(deal)
    await db.flush()

    purchase = SkillMarketplacePurchase(
        buyer_tenant_id=buyer_tenant_id,
        seller_tenant_id=publication.owner_tenant_id,
        publication_id=publication.id,
        employee_id=employee_id,
        skill_package_id=package.id,
        product_id=product.id,
        business_deal_id=deal.id,
        idempotency_key=key,
        status=SkillMarketplacePurchaseStatus.PENDING,
        amount=amount,
        currency=currency,
        metadata_={"customer_acceptance": "not_implied"},
    )
    db.add(purchase)
    await db.flush()
    deal_metadata = dict(deal.metadata_ or {})
    deal_metadata["skill_marketplace_purchase"]["purchase_id"] = str(purchase.id)
    deal.metadata_ = deal_metadata
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=buyer_tenant_id,
        actor_id=actor_id,
        action="skill_marketplace_purchase.prepared",
        resource_type="skill_marketplace_purchase",
        resource_id=str(purchase.id),
        metadata={
            "buyer_tenant_id": str(buyer_tenant_id),
            "seller_tenant_id": str(publication.owner_tenant_id),
            "publication_id": str(publication.id),
            "employee_id": str(employee_id),
            "product_id": str(product.id),
            "skill_package_id": str(package.id),
            "amount": float(amount),
            "currency": currency,
            "customer_acceptance": "not_implied",
            "execution_authority_changed": False,
        },
    )
    return purchase, deal, False


async def create_checkout(
    db: AsyncSession,
    *,
    buyer_tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    publication_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    customer_email: str | None,
    idempotency_key: str,
):
    purchase, deal, replay = await prepare_purchase(
        db,
        buyer_tenant_id=buyer_tenant_id,
        employee_id=employee_id,
        publication_id=publication_id,
        actor_id=actor_id,
        customer_email=customer_email,
        idempotency_key=idempotency_key,
    )
    if replay and purchase.status == SkillMarketplacePurchaseStatus.PAID:
        return purchase, deal, None, True

    await db.commit()
    try:
        result = await create_sales_checkout_session(
            tenant_id=buyer_tenant_id,
            deal_id=deal.id,
            amount=purchase.amount,
            currency=purchase.currency,
            customer_email=customer_email,
            idempotency_key=idempotency_key,
            db=db,
        )
    except Exception:
        await db.rollback()
        raise

    purchase.provider = result.provider
    metadata = dict(purchase.metadata_ or {})
    metadata["provider_execution"] = result.provider_execution
    metadata["checkout_created"] = bool(result.checkout_url)
    purchase.metadata_ = metadata
    await db.commit()
    return purchase, deal, result, replay

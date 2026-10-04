"""Real-stack HTTP API verification for cross-tenant Skill Marketplace purchase."""
from __future__ import annotations

import asyncio
import json
import os
import time
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.business_deal import BusinessDeal
from app.models.product import Product
from app.models.skill_marketplace_purchase import (
    SkillMarketplacePurchase,
    SkillMarketplacePurchaseStatus,
)
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.models.tenant import Tenant
from app.models.skill_package import SkillPackage
from app.services import edition_lifecycle_service, skill_marketplace_service

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def assert_status(actual: int, expected: int, label: str, body: dict) -> None:
    assert actual == expected, f"{label}: expected HTTP {expected}, got {actual}: {body}"


def register(suffix: str, label: str) -> tuple[str, str, str]:
    slug = f"w16-marketplace-api-{label}-{suffix}"
    status, response = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"W16 Marketplace API {label} Tenant",
            "tenant_slug": slug,
            "email": f"w16-marketplace-api-{label}-{suffix}@example.com",
            "password": "W16MarketplaceApiE2E-2026!",
            "full_name": f"W16 Marketplace API {label} Admin",
        },
    )
    assert_status(status, 201, f"{label} registration", response)
    data = response.get("data") or {}
    token = data.get("access_token")
    assert token
    return slug, token, data.get("user", {}).get("id") or ""


async def seller_fixture(seller_slug: str) -> tuple[str, str]:
    async with AsyncSessionLocal() as db:
        seller = (
            await db.execute(
                select(Tenant).where(Tenant.slug == seller_slug)
            )
        ).scalar_one()

        slug = f"api-marketplace-skill-{seller.id.hex[:8]}-{time.time_ns() % 10000}"
        product = Product(
            tenant_id=seller.id,
            sku=f"api-marketplace-product-{time.time_ns() % 100000}",
            name="API Marketplace Skill",
            description="Cross-tenant HTTP API fixture",
            category="employee_skill",
            price=Decimal("19.00"),
            currency="EUR",
            inventory=25,
            attributes={
                "skill_package_slug": slug,
                "skill_package_version": 1,
            },
            is_active=True,
        )
        db.add(product)
        await db.flush()

        package = await skill_marketplace_service.create_package(
            db,
            tenant_id=seller.id,
            slug=slug,
            name="API Marketplace Skill",
            version=1,
            product_id=product.id,
        )
        await skill_marketplace_service.publish_package(
            db,
            tenant_id=seller.id,
            package_id=package.id,
            actor_id=None,
        )
        await db.commit()
        return str(package.id), str(product.id)


async def cleanup(slugs: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        tenants = list(
            (
                await db.execute(
                    select(Tenant).where(Tenant.slug.in_(slugs))
                )
            ).scalars().all()
        )
        for tenant in tenants:
            if tenant.status != edition_lifecycle_service.STATUS_DEPROVISIONED:
                await edition_lifecycle_service.transition_tenant_status(
                    db,
                    tenant=tenant,
                    target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
                    actor_id=None,
                    audit_tenant_id=tenant.id,
                    audit_metadata={
                        "certification_fixture": True,
                        "cleanup_mode": "deprovision",
                    },
                )
        await db.commit()


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    slugs: list[str] = []
    try:
        seller_slug, seller_token, seller_user_id = register(suffix, "seller")
        buyer_slug, buyer_token, buyer_user_id = register(suffix, "buyer")
        slugs.extend([seller_slug, buyer_slug])

        status, seller_employee = request(
            "POST",
            "/employees",
            {
                "slug": f"seller-employee-{suffix}",
                "name": "Seller Employee",
                "kind": "custom",
                "input_schema": {},
                "output_schema": {},
                "prompt_template": "Marketplace seller fixture",
                "allowed_tools": [],
                "rules": {},
            },
            token=seller_token,
        )
        assert_status(status, 201, "seller employee create", seller_employee)
        seller_employee_id = (seller_employee.get("data") or {}).get("id")
        assert seller_employee_id

        status, buyer_employee = request(
            "POST",
            "/employees",
            {
                "slug": f"buyer-employee-{suffix}",
                "name": "Buyer Employee",
                "kind": "custom",
                "input_schema": {},
                "output_schema": {},
                "prompt_template": "Marketplace buyer fixture",
                "allowed_tools": [],
                "rules": {},
            },
            token=buyer_token,
        )
        assert_status(status, 201, "buyer employee create", buyer_employee)
        buyer_employee_id = (buyer_employee.get("data") or {}).get("id")
        assert buyer_employee_id

        package_id, product_id = asyncio.run(seller_fixture(seller_slug))

        status, publication = request(
            "POST",
            "/skill-marketplace/publications",
            {
                "skill_package_id": package_id,
                "visibility": "public",
                "title": "API Marketplace Skill",
                "summary": "Public HTTP purchase fixture",
            },
            token=seller_token,
        )
        assert_status(status, 201, "seller publication", publication)
        publication_id = (publication.get("data") or {}).get("id")
        assert publication_id
        print("SELLER PUBLICATION VIA HTTP API PASS")

        status, public_view = request(
            "GET",
            f"/skill-marketplace/publications/{publication_id}",
            token=buyer_token,
        )
        assert_status(status, 200, "buyer public publication lookup", public_view)
        public_data = public_view.get("data") or {}
        assert public_data.get("id") == publication_id
        assert public_data.get("skill_package_id") == package_id
        print("BUYER PUBLIC DISCOVERY VIA HTTP API PASS")

        idempotency_key = f"w16-marketplace-api-{suffix}"
        payload = {
            "publication_id": publication_id,
            "employee_id": buyer_employee_id,
            "idempotency_key": idempotency_key,
        }

        status, purchase_response = request(
            "POST",
            "/skill-marketplace/publications/purchases",
            payload,
            token=buyer_token,
        )
        assert_status(status, 201, "buyer marketplace purchase", purchase_response)
        purchase_data = purchase_response.get("data") or {}
        assert purchase_data.get("buyer_tenant_id")
        assert purchase_data.get("seller_tenant_id")
        assert purchase_data["buyer_tenant_id"] != purchase_data["seller_tenant_id"]
        assert purchase_data["employee_id"] == buyer_employee_id
        assert purchase_data["skill_package_id"] == package_id
        assert purchase_data["product_id"] == product_id
        assert purchase_data["status"] == "pending"
        assert purchase_data["provider"] == "contract-test"
        assert purchase_data["executed"] is False
        assert purchase_data["idempotent_replay"] is False
        first_purchase_id = purchase_data["purchase_id"]
        first_deal_id = purchase_data["deal_id"]
        print("CROSS-TENANT MARKETPLACE PURCHASE VIA HTTP API PASS")

        status, replay_response = request(
            "POST",
            "/skill-marketplace/publications/purchases",
            payload,
            token=buyer_token,
        )
        assert_status(status, 201, "buyer marketplace purchase replay", replay_response)
        replay_data = replay_response.get("data") or {}
        assert replay_data["purchase_id"] == first_purchase_id
        assert replay_data["deal_id"] == first_deal_id
        assert replay_data["idempotent_replay"] is True
        print("MARKETPLACE PURCHASE HTTP IDEMPOTENCY PASS")

        status, own_purchase = request(
            "POST",
            "/skill-marketplace/publications/purchases",
            {
                "publication_id": publication_id,
                "employee_id": seller_employee_id,
                "idempotency_key": f"w16-marketplace-own-{suffix}",
            },
            token=seller_token,
        )
        assert own_purchase
        assert_status(status, 409, "seller self-purchase rejection", own_purchase)
        print("MARKETPLACE SELF-PURCHASE REJECT PASS")

        async def db_assertions() -> None:
            async with AsyncSessionLocal() as db:
                purchase = await db.get(SkillMarketplacePurchase, first_purchase_id)
                assert purchase is not None
                assert str(purchase.buyer_tenant_id) == purchase_data["buyer_tenant_id"]
                assert str(purchase.seller_tenant_id) == purchase_data["seller_tenant_id"]
                assert purchase.status == SkillMarketplacePurchaseStatus.PENDING

                deal = await db.get(BusinessDeal, first_deal_id)
                assert deal is not None
                assert str(deal.tenant_id) == purchase_data["buyer_tenant_id"]
                assert (deal.metadata_ or {}).get("skill_marketplace_purchase", {}).get("purchase_id") == first_purchase_id

                publication = await db.get(SkillMarketplacePublication, publication_id)
                package = await db.get(SkillPackage, package_id)
                assert publication is not None
                assert package is not None
                assert str(publication.owner_tenant_id) == purchase_data["seller_tenant_id"]
                assert str(package.tenant_id) == purchase_data["seller_tenant_id"]

        asyncio.run(db_assertions())
        print("MARKETPLACE BUYER/SELLER DURABLE CORRELATION PASS")
        print("W16 CROSS-TENANT MARKETPLACE PURCHASE HTTP REAL-STACK PASS")
        return 0
    finally:
        try:
            asyncio.run(cleanup(slugs))
        except Exception as exc:
            print(f"MARKETPLACE HTTP FIXTURE CLEANUP FAIL: {type(exc).__name__}")


if __name__ == "__main__":
    raise SystemExit(main())

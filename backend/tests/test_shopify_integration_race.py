"""Real PostgreSQL concurrency coverage for Shopify integration identity."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.core.exceptions import ConflictError
from app.models.commerce_integration import CommerceIntegration
from app.models.tenant import Tenant
from app.services import commerce_integration_service


@pytest_asyncio.fixture
async def shopify_integration_race_setup(monkeypatch):
    async def record(*_args, **_kwargs):
        return None

    monkeypatch.setattr(commerce_integration_service.audit_service, "record", record)

    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            name="Shopify Integration Race Test",
            slug=f"shopify-integration-race-{uuid.uuid4().hex[:12]}",
            status="active",
        )
        db.add(tenant)
        await db.commit()
        tenant_id = tenant.id

    yield tenant_id

    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(CommerceIntegration).where(
                CommerceIntegration.tenant_id == tenant_id
            )
        )
        await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()


@pytest.mark.asyncio
async def test_concurrent_shopify_creation_allows_only_one_instance(
    shopify_integration_race_setup,
):
    tenant_id = shopify_integration_race_setup

    async def create_one(index: int):
        async with AsyncSessionLocal() as db:
            try:
                row = await commerce_integration_service.create_integration(
                    db,
                    tenant_id=tenant_id,
                    provider="shopify",
                    name=f"Store {index}",
                    config={"shop_domain": f"store-{index}.myshopify.com"},
                )
                await db.commit()
                return "created", row.id
            except ConflictError:
                await db.rollback()
                return "conflict", None

    results = await asyncio.gather(create_one(1), create_one(2))

    assert sorted(result[0] for result in results) == ["conflict", "created"]

    async with AsyncSessionLocal() as db:
        rows = list(
            (
                await db.execute(
                    select(CommerceIntegration).where(
                        CommerceIntegration.tenant_id == tenant_id,
                        CommerceIntegration.provider == "shopify",
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_non_shopify_providers_remain_independently_repeatable(
    shopify_integration_race_setup,
):
    tenant_id = shopify_integration_race_setup

    async with AsyncSessionLocal() as db:
        first = await commerce_integration_service.create_integration(
            db,
            tenant_id=tenant_id,
            provider="custom_api",
            name="Custom A",
            config={},
        )
        second = await commerce_integration_service.create_integration(
            db,
            tenant_id=tenant_id,
            provider="custom_api",
            name="Custom B",
            config={},
        )
        await db.commit()

    assert first.id != second.id

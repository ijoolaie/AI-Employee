"""PostgreSQL-backed acceptance for verified public customer order access.

Runs only against the dedicated local support_test database. No real SMTP
connection is made; verification mail is asserted at the durable outbox boundary.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _support_test_database_url() -> str:
    url = os.environ.get("SUPPORT_TEST_DATABASE_URL")
    if not url:
        pytest.skip("SUPPORT_TEST_DATABASE_URL is not configured")
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433}
        or parsed.database != "support_test"
        or parsed.username not in {"support_test_user", "aiep"}
        or not parsed.password
    ):
        raise RuntimeError("Refusing to run public customer verification test outside support_test")
    return url


@pytest.mark.asyncio
async def test_verified_email_links_only_unique_tenant_customer_and_scoped_orders(monkeypatch):
    from app.models.business_order import BusinessOrder
    from app.models.commerce_integration import CommerceIntegration
    from app.models.conversation import CustomerConversation
    from app.models.customer import Customer
    from app.models.customer_channel import CustomerChannel
    from app.models.customer_email_verification import CustomerEmailVerification
    from app.models.employee import Employee
    from app.models.outbox import OutboxMessage
    from app.models.tenant import Tenant
    from app.services import customer_channel_service

    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    token = f"verified-customer-{suffix}"
    email = f"buyer-{suffix}@example.com"
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        customer_channel_service,
        "get_settings",
        lambda: SimpleNamespace(
            secret_key="dedicated-test-secret-with-sufficient-entropy",
            smtp_host="smtp.test.invalid",
            smtp_from_email="support@example.com",
        ),
    )
    try:
        async with sessions() as session:
            async with session.begin():
                tenant = Tenant(
                    id=uuid.uuid4(), name=f"Verification tenant {suffix}",
                    slug=f"verification-{suffix}", tenant_kind="customer", status="active",
                )
                session.add(tenant)
                await session.flush()
                employee = Employee(
                    id=uuid.uuid4(), tenant_id=tenant.id,
                    slug=f"verification-agent-{suffix}", name="Verification test agent",
                    kind="custom", is_active=True,
                )
                session.add(employee)
                await session.flush()
                channel = CustomerChannel(
                    id=uuid.uuid4(), tenant_id=tenant.id, employee_id=employee.id,
                    name="Verified customer test", channel_type="web_widget",
                    public_key=f"pk_verify_{suffix}",
                    config={"support_policy": {"commerce": {"max_order_staleness_seconds": 3600}}},
                    is_active=True,
                )
                customer = Customer(
                    id=uuid.uuid4(), tenant_id=tenant.id, external_key=f"shopify-customer-{suffix}",
                    name="Synthetic buyer", email=email, last_channel="shopify", is_active=True,
                )
                other_customer = Customer(
                    id=uuid.uuid4(), tenant_id=tenant.id, external_key=f"other-shopify-customer-{suffix}",
                    name="Different synthetic buyer", email=f"other-{suffix}@example.com",
                    last_channel="shopify", is_active=True,
                )
                session.add_all([channel, customer, other_customer])
                await session.flush()
                conversation = CustomerConversation(
                    id=uuid.uuid4(), tenant_id=tenant.id, employee_id=employee.id,
                    channel_id=channel.id, customer_token_hash=customer_channel_service._hash_token(token),
                    customer_email=email, customer_id=None, status="open", handoff_requested=False,
                )
                integration = CommerceIntegration(
                    id=uuid.uuid4(), tenant_id=tenant.id, provider="shopify",
                    name="Synthetic Shopify", status="synced", is_active=True,
                    config={"last_order_sync_at": now.isoformat()},
                )
                session.add_all([conversation, integration])
                await session.flush()
                session.add_all([
                    BusinessOrder(
                        tenant_id=tenant.id, number=f"OWN-{suffix}", status="processing",
                        currency="EUR", customer_name="Synthetic buyer", customer_email=email,
                        order_date=date.today(), total=Decimal("25.00"),
                        metadata_={"shopify": True, "customer_id": str(customer.id)},
                    ),
                    BusinessOrder(
                        tenant_id=tenant.id, number=f"OTHER-{suffix}", status="processing",
                        currency="EUR", customer_name="Different buyer",
                        customer_email=other_customer.email, order_date=date.today(),
                        total=Decimal("99.00"),
                        metadata_={"shopify": True, "customer_id": str(other_customer.id)},
                    ),
                ])
                await session.flush()

                await customer_channel_service.request_customer_email_verification(
                    session, conversation_id=conversation.id, token=token,
                )
                mail = (await session.execute(
                    select(OutboxMessage).where(
                        OutboxMessage.tenant_id == tenant.id,
                        OutboxMessage.kind == "email.send",
                        OutboxMessage.dedupe_key == f"customer-email-verification:{session.new.pop().id if False else ''}",
                    )
                )).scalar_one_or_none()
                # Resolve the newest verification challenge and its durable email.
                challenge = (await session.execute(
                    select(CustomerEmailVerification).where(
                        CustomerEmailVerification.tenant_id == tenant.id,
                        CustomerEmailVerification.conversation_id == conversation.id,
                    )
                )).scalar_one()
                mail = (await session.execute(
                    select(OutboxMessage).where(
                        OutboxMessage.tenant_id == tenant.id,
                        OutboxMessage.dedupe_key == f"customer-email-verification:{challenge.id}",
                    )
                )).scalar_one()
                code = mail.payload["body"].split("code is: ", 1)[1].splitlines()[0]
                assert mail.payload["to"] == [email]
                assert challenge.code_hash != code

                verified = await customer_channel_service.verify_customer_email(
                    session, conversation_id=conversation.id, token=token, code="000000" if code != "000000" else "000001",
                )
                assert verified is False
                assert challenge.attempts == 1

                verified = await customer_channel_service.verify_customer_email(
                    session, conversation_id=conversation.id, token=token, code=code,
                )
                assert verified is True
                assert conversation.customer_id == customer.id
                assert conversation.verified_email == email
                assert conversation.email_verified_at is not None

                orders = await customer_channel_service.get_public_customer_orders(
                    session, conversation_id=conversation.id, token=token,
                )
                assert orders["available"] is True
                assert [row["number"] for row in orders["orders"]] == [f"OWN-{suffix}"]
                assert orders["source_fresh_at"] == now

                # Stale provider evidence must fail closed even after identity verification.
                integration.config = {
                    "last_order_sync_at": (now - timedelta(hours=2)).isoformat(),
                }
                await session.flush()
                stale_orders = await customer_channel_service.get_public_customer_orders(
                    session, conversation_id=conversation.id, token=token,
                )
                assert stale_orders["available"] is False
                assert stale_orders["orders"] == []
    finally:
        await engine.dispose()

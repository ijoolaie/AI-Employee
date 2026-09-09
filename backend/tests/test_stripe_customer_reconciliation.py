import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import ConflictError
from app.models.billing import Subscription
from app.services import stripe_service


@pytest.mark.asyncio
async def test_customer_reconciliation_recovers_existing_customer():
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000123")
    sub = Subscription(provider_customer_id=None)
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                SimpleNamespace(scalar_one=lambda: sub),
                SimpleNamespace(scalar_one_or_none=lambda: SimpleNamespace(name="Acme")),
            ]
        ),
        flush=AsyncMock(),
    )
    search = Mock(return_value=SimpleNamespace(data=[SimpleNamespace(id="cus_existing")]))
    create = Mock()
    stripe = SimpleNamespace(Customer=SimpleNamespace(search=search, create=create))

    result = await stripe_service._get_or_create_stripe_customer(
        db, stripe, tenant_id=tenant_id, sub=sub, user_email="test@example.test"
    )

    assert result == "cus_existing"
    assert sub.provider_customer_id == "cus_existing"
    search.assert_called_once_with(query=f"metadata['tenant_id']:'{tenant_id}'", limit=2)
    create.assert_not_called()
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_customer_reconciliation_fails_closed_on_multiple_matches():
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000123")
    sub = Subscription(provider_customer_id=None)
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                SimpleNamespace(scalar_one=lambda: sub),
                SimpleNamespace(scalar_one_or_none=lambda: SimpleNamespace(name="Acme")),
            ]
        ),
        flush=AsyncMock(),
    )
    search = Mock(return_value=SimpleNamespace(data=[SimpleNamespace(id="cus_a"), SimpleNamespace(id="cus_b")]))
    create = Mock()
    stripe = SimpleNamespace(Customer=SimpleNamespace(search=search, create=create))

    with pytest.raises(ConflictError):
        await stripe_service._get_or_create_stripe_customer(
            db, stripe, tenant_id=tenant_id, sub=sub, user_email=None
        )

    create.assert_not_called()


@pytest.mark.asyncio
async def test_customer_reconciliation_falls_back_to_tenant_idempotency_on_search_miss():
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000123")
    sub = Subscription(provider_customer_id=None)
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                SimpleNamespace(scalar_one=lambda: sub),
                SimpleNamespace(scalar_one_or_none=lambda: SimpleNamespace(name="Acme")),
            ]
        ),
        flush=AsyncMock(),
    )
    search = Mock(return_value=SimpleNamespace(data=[]))
    create = Mock(return_value=SimpleNamespace(id="cus_created"))
    stripe = SimpleNamespace(Customer=SimpleNamespace(search=search, create=create))

    result = await stripe_service._get_or_create_stripe_customer(
        db, stripe, tenant_id=tenant_id, sub=sub, user_email="test@example.test"
    )

    assert result == "cus_created"
    assert sub.provider_customer_id == "cus_created"
    create.assert_called_once_with(
        email="test@example.test",
        name="Acme",
        metadata={"tenant_id": str(tenant_id)},
        idempotency_key=f"customer:{tenant_id}",
    )
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_customer_reconciliation_rechecks_locked_subscription_before_provider_call():
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000123")
    sub = Subscription(provider_customer_id="cus_winner")
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one=lambda: sub)),
        flush=AsyncMock(),
    )
    search = Mock()
    create = Mock()
    stripe = SimpleNamespace(Customer=SimpleNamespace(search=search, create=create))

    result = await stripe_service._get_or_create_stripe_customer(
        db, stripe, tenant_id=tenant_id, sub=sub, user_email="test@example.test"
    )

    assert result == "cus_winner"
    search.assert_not_called()
    create.assert_not_called()
    db.execute.assert_awaited_once()

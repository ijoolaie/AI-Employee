from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import billing_service


@pytest.mark.asyncio
async def test_existing_subscription_is_locked_before_lifecycle_mutation():
    db = AsyncMock()
    subscription = SimpleNamespace(id="sub-1")
    result = SimpleNamespace(scalar_one_or_none=lambda: subscription)
    db.execute.return_value = result

    lifecycle = AsyncMock(return_value=subscription)

    original = billing_service.process_subscription_lifecycle
    billing_service.process_subscription_lifecycle = lifecycle
    try:
        returned = await billing_service.ensure_subscription(
            db,
            tenant_id="00000000-0000-0000-0000-000000000001",
        )
    finally:
        billing_service.process_subscription_lifecycle = original

    assert returned is subscription
    statement = db.execute.await_args.args[0]
    assert statement._for_update_arg is not None
    lifecycle.assert_awaited_once_with(db, subscription=subscription)

from datetime import datetime, timezone, timedelta

import pytest

from app.models.billing import Subscription
from app.services.billing_service import process_subscription_lifecycle
from app.services.release_channel_service import CURRENT_RELEASE_VERSION, default_policies


@pytest.mark.parametrize("channel", ["vendor", "reseller", "customer"])
def test_v120_is_the_only_certified_commercial_release(channel):
    policy = default_policies()[channel]
    assert policy.is_supported(CURRENT_RELEASE_VERSION)
    assert not policy.is_supported("v1.1.2")


@pytest.mark.asyncio
async def test_external_subscription_does_not_auto_renew_without_provider_event():
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        tenant_id="00000000-0000-0000-0000-000000000001",
        plan_id="00000000-0000-0000-0000-000000000002",
        status="active",
        provider="stripe",
        current_period_start=now - timedelta(days=31),
        current_period_end=now - timedelta(days=1),
        cancel_at_period_end=False,
    )

    class FakeDB:
        flushed = False

        async def flush(self):
            self.flushed = True

    db = FakeDB()
    result = await process_subscription_lifecycle(db, subscription=subscription, now=now)

    assert result.status == "active"
    assert result.current_period_end == subscription.current_period_end
    assert db.flushed is False

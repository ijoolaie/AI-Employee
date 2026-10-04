import asyncio
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import skill_marketplace_reporting_service


@pytest.mark.asyncio
async def test_marketplace_financial_summary_is_read_only_and_settlement_based():
    class Result:
        def __init__(self, value):
            self.value = value
        def all(self):
            return self.value
        def scalar_one(self):
            return self.value

    class DB:
        def __init__(self):
            self.calls = 0
        async def execute(self, stmt):
            self.calls += 1
            if self.calls == 1:
                return Result([("EUR", 2, Decimal("20.00"), Decimal("3.00"), Decimal("17.00"))])
            if self.calls == 2:
                return Result(2)
            if self.calls == 3:
                return Result(2)
            return Result(0)

    data = await skill_marketplace_reporting_service.marketplace_financial_summary(
        DB(),
        platform_admin_tenant_id=uuid4(),
    )
    assert data["verified_settlement_count"] == 2
    assert data["verified_paid_purchase_count"] == 2
    assert data["by_currency"]["EUR"]["gross_amount"] == "20.00"
    assert data["by_currency"]["EUR"]["platform_fee_amount"] == "3.00"
    assert data["by_currency"]["EUR"]["seller_net_amount"] == "17.00"
    assert data["external_customer_revenue_verified"] is False
    assert data["external_seller_payout_verified"] is False
    assert data["execution_authority_changed"] is False


def test_reporting_module_contains_no_payment_provider_calls():
    import inspect
    source = inspect.getsource(skill_marketplace_reporting_service.marketplace_financial_summary)
    assert "stripe" not in source.lower()
    assert "zarinpal" not in source.lower()

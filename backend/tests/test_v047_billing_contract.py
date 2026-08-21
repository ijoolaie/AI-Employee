"""Phase 4 Monetization contracts: plans, idempotent billing events and quotas."""

from decimal import Decimal

from app.schemas.billing import BillingEventRequest, PlanResponse, SubscribeRequest
from app.services.billing_service import PLAN_SEEDS


def test_phase4_defines_three_roadmap_plans():
    assert [p["code"] for p in PLAN_SEEDS] == ["starter", "business", "professional"]
    assert PLAN_SEEDS[0]["monthly_price_usd"] == Decimal("0.00")
    assert PLAN_SEEDS[1]["monthly_price_usd"] > 0
    assert PLAN_SEEDS[2]["monthly_price_usd"] > PLAN_SEEDS[1]["monthly_price_usd"]


def test_plan_contract_is_serializable():
    result = PlanResponse.model_validate(PLAN_SEEDS[1])
    assert result.code == "business"
    assert result.monthly_runs > 0
    assert result.monthly_tokens > result.monthly_runs


def test_subscription_change_contract():
    assert SubscribeRequest(plan_code="professional").plan_code == "professional"


def test_billing_event_requires_idempotency_identity():
    event = BillingEventRequest(
        provider="test",
        provider_event_id="evt-1",
        event_type="subscription.updated",
    )
    assert event.provider_event_id == "evt-1"

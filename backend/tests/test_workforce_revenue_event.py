from decimal import Decimal
import uuid

from app.models.workforce_revenue_event import WorkforceRevenueEvent


def test_workforce_revenue_event_is_independent_business_outcome_ledger():
    tenant_id = uuid.uuid4()
    event = WorkforceRevenueEvent(
        tenant_id=tenant_id,
        deal_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        provider="stripe",
        provider_event_id="evt_test_revenue_1",
        amount=Decimal("100.00"),
        currency="USD",
        source="stripe_verified_sales_payment",
        metadata_={"source": "ai_workforce"},
    )

    assert event.tenant_id == tenant_id
    assert event.provider == "stripe"
    assert event.amount == Decimal("100.00")
    assert event.metadata_["source"] == "ai_workforce"

    constraints = {c.name for c in WorkforceRevenueEvent.__table__.constraints}
    assert "uq_workforce_revenue_event_provider_id" in constraints

def test_workforce_revenue_event_is_tenant_scoped():
    assert "ix_workforce_revenue_event_tenant" in {i.name for i in WorkforceRevenueEvent.__table__.indexes}

def test_workforce_revenue_event_source_is_bounded():
    assert WorkforceRevenueEvent.__table__.c.source.type.length == 64

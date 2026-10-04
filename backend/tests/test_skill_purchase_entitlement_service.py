"""W16 verified skill purchase entitlement contract tests."""
import inspect
import uuid

import pytest

from app.models.skill_purchase_entitlement import (
    SkillPurchaseEntitlement,
    SkillPurchaseEntitlementStatus,
)
from app.services import skill_marketplace_service, stripe_service
from app.services.skill_purchase_entitlement_service import (
    grant_from_verified_payment,
)


def test_skill_purchase_entitlement_is_presentation_only():
    columns = {column.name for column in SkillPurchaseEntitlement.__table__.columns}
    assert "permission" not in columns
    assert "allowed_tools" not in columns
    assert "capability_contract" not in columns
    assert "approval_policy" not in columns
    assert "tool_bindings" not in columns


def test_skill_purchase_entitlement_has_tenant_employee_package_scope():
    columns = SkillPurchaseEntitlement.__table__.c
    assert "tenant_id" in columns
    assert "employee_id" in columns
    assert "skill_package_id" in columns
    names = {constraint.name for constraint in SkillPurchaseEntitlement.__table__.constraints}
    assert "uq_skill_purchase_entitlement" in names


def test_commercial_skill_install_requires_verified_entitlement():
    source = inspect.getsource(skill_marketplace_service.install)
    assert "verified purchase entitlement" in source
    assert "assert_owned" in source
    assert "package.product_id is not None" in source


def test_verified_payment_settlement_grants_skill_ownership_before_payment_marker():
    source = inspect.getsource(stripe_service.apply_verified_sales_payment)
    grant_marker = source.index("skill_purchase_entitlement_service")
    payment_marker = source.index('deal_metadata["payment_verified"] = True')
    assert grant_marker < payment_marker
    assert "amount != Decimal(str(deal.amount))" in source[:grant_marker]
    assert "provider_event_id" in source[:grant_marker]


@pytest.mark.asyncio
async def test_skill_grant_replay_is_blocked_by_deal_marker(monkeypatch):
    tenant_id = uuid.uuid4()
    entitlement_id = uuid.uuid4()
    source_order_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    product_id = uuid.uuid4()
    skill_package_id = uuid.uuid4()

    class Deal:
        metadata_ = {
            "skill_purchase": {
                "employee_id": str(employee_id),
                "product_id": str(product_id),
                "skill_package_id": str(skill_package_id),
            }
        }

    async def fake_grant(*_args, **kwargs):
        assert kwargs["tenant_id"] == tenant_id
        assert kwargs["employee_id"] == employee_id
        assert kwargs["skill_package_id"] == skill_package_id
        assert kwargs["source_order_id"] == source_order_id
        return type("Entitlement", (), {"id": entitlement_id})()

    monkeypatch.setattr(
        "app.services.skill_purchase_entitlement_service.SkillPurchaseEntitlement",
        SkillPurchaseEntitlement,
    )

    # The settlement function must not call the lower-level ledger twice for
    # the same governed deal. Patch the lower-level DB-dependent path instead.
    monkeypatch.setattr(
        "app.services.skill_purchase_entitlement_service.audit_service.record",
        lambda *args, **kwargs: None,
    )

    # First prove the contract marker short-circuit independently of DB access.
    deal = Deal()
    deal.metadata_["skill_entitlement_granted"] = True
    class DB:
        async def flush(self):
            return None

    assert await grant_from_verified_payment(
        DB(),
        tenant_id=tenant_id,
        deal=deal,
        source_order_id=source_order_id,
        provider="stripe",
        provider_event_id="evt_test",
    ) is None

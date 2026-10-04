"""W15 ownership ledger contract tests."""
import inspect
import uuid

import pytest

from app.models.cosmetic_entitlement import CosmeticEntitlement
from app.schemas.deal import CosmeticPurchase
from app.services.cosmetic_entitlement_service import (
    COSMETIC_VALUES,
    CosmeticEntitlementError,
    _validate_cosmetic,
    _validate_product_contract,
    grant,
    grant_from_verified_payment,
)


def test_cosmetic_entitlement_model_is_presentation_only():
    columns = {column.name for column in CosmeticEntitlement.__table__.columns}
    assert "permission" not in columns
    assert "capability" not in columns
    assert "tool_name" not in columns
    assert "approval" not in columns


def test_invalid_cosmetic_value_rejected():
    with pytest.raises(CosmeticEntitlementError, match="cosmetic value"):
        _validate_cosmetic("outfit", "admin")


def test_tenant_and_employee_scope_are_explicit():
    assert "tenant_id" in CosmeticEntitlement.__table__.c
    assert "employee_id" in CosmeticEntitlement.__table__.c
    assert "product_id" in CosmeticEntitlement.__table__.c


def test_idempotent_regrant_contract_is_unique():
    names = {constraint.name for constraint in CosmeticEntitlement.__table__.constraints}
    assert "uq_cosmetic_entitlement_tenant_employee_product" in names


def test_presentation_values_match_w14_contract():
    assert COSMETIC_VALUES["outfit"] == {"business", "casual", "technical", "formal"}
    assert COSMETIC_VALUES["accessory"] == {"none", "glasses", "headset", "badge"}


def test_product_must_explicitly_declare_matching_cosmetic_contract():
    class ProductStub:
        is_active = True
        category = "employee_cosmetic"
        attributes = {"cosmetic_type": "accessory", "cosmetic_value": "glasses"}

    _validate_product_contract(ProductStub(), "accessory", "glasses")

    with pytest.raises(CosmeticEntitlementError, match="does not match"):
        _validate_product_contract(ProductStub(), "outfit", "business")


@pytest.mark.asyncio
async def test_cross_tenant_employee_is_rejected_before_product_lookup():
    class Result:
        def scalar_one_or_none(self):
            return None

    class DB:
        async def execute(self, _stmt):
            return Result()

    with pytest.raises(CosmeticEntitlementError, match="employee not found"):
        await grant(
            DB(),
            tenant_id=uuid.uuid4(),
            employee_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            cosmetic_type="accessory",
            cosmetic_value="glasses",
        )


def test_cosmetic_purchase_schema_is_bounded():
    payload = {
        "employee_id": uuid.uuid4(),
        "product_id": uuid.uuid4(),
        "cosmetic_type": "accessory",
        "cosmetic_value": "glasses",
    }
    assert CosmeticPurchase.model_validate(payload).cosmetic_type == "accessory"
    with pytest.raises(Exception):
        CosmeticPurchase.model_validate({**payload, "permission": "admin"})


@pytest.mark.asyncio
async def test_verified_payment_grant_is_idempotent_at_deal_marker(monkeypatch):
    entitlement_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    product_id = uuid.uuid4()

    class Deal:
        metadata_ = {
            "cosmetic_purchase": {
                "employee_id": str(employee_id),
                "product_id": str(product_id),
                "cosmetic_type": "accessory",
                "cosmetic_value": "glasses",
            }
        }

    async def fake_grant(*_args, **kwargs):
        assert kwargs["tenant_id"] == tenant_id
        assert kwargs["employee_id"] == employee_id
        assert kwargs["product_id"] == product_id
        assert kwargs["source_order_id"] == source_order_id
        return type("Entitlement", (), {"id": entitlement_id})()

    source_order_id = uuid.uuid4()
    monkeypatch.setattr(
        "app.services.cosmetic_entitlement_service.grant",
        fake_grant,
    )
    deal = Deal()
    entitlement = await grant_from_verified_payment(
        object(),
        tenant_id=tenant_id,
        deal=deal,
        source_order_id=source_order_id,
    )
    assert entitlement.id == entitlement_id
    assert deal.metadata_["cosmetic_entitlement_granted"] is True
    assert deal.metadata_["cosmetic_entitlement_id"] == str(entitlement_id)
    assert deal.metadata_["presentation_only"] is True

    # A replay against the same governed deal must not invoke grant again.
    async def fail_grant(*_args, **_kwargs):
        raise AssertionError("grant must not run on an already-settled cosmetic purchase")

    monkeypatch.setattr(
        "app.services.cosmetic_entitlement_service.grant",
        fail_grant,
    )
    assert await grant_from_verified_payment(
        object(),
        tenant_id=tenant_id,
        deal=deal,
        source_order_id=source_order_id,
    ) is None


def test_verified_payment_integration_is_after_provider_verification():
    from app.services import stripe_service

    source = inspect.getsource(stripe_service.apply_verified_sales_payment)
    payment_marker = source.index('deal_metadata["payment_verified"] = True')
    grant_marker = source.index("grant_from_verified_payment")
    assert grant_marker < payment_marker
    assert "provider_event_id" in source[:grant_marker]
    assert "amount != Decimal(str(deal.amount))" in source[:grant_marker]


def test_apply_entitlement_is_presentation_only():
    from app.services import cosmetic_entitlement_service

    source = inspect.getsource(cosmetic_entitlement_service.apply_entitlement)
    assert "presentation_profile" in source
    assert "permission" not in source
    assert "capability" not in source
    assert "tool" not in source
    assert "approval" not in source

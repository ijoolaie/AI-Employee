"""W15 ownership ledger contract tests."""
import uuid

import pytest

from app.models.cosmetic_entitlement import CosmeticEntitlement
from app.services.cosmetic_entitlement_service import (
    CosmeticEntitlementError,
    grant,
    list_for_employee,
    revoke,
)


def test_cosmetic_entitlement_model_is_presentation_only():
    columns = {column.name for column in CosmeticEntitlement.__table__.columns}
    assert "permission" not in columns
    assert "capability" not in columns
    assert "tool_name" not in columns
    assert "approval" not in columns


def test_invalid_cosmetic_value_rejected():
    with pytest.raises(CosmeticEntitlementError, match="cosmetic value"):
        from app.services.cosmetic_entitlement_service import _validate_cosmetic

        _validate_cosmetic("outfit", "admin")


def test_tenant_and_employee_scope_are_explicit():
    assert "tenant_id" in CosmeticEntitlement.__table__.c
    assert "employee_id" in CosmeticEntitlement.__table__.c
    assert "product_id" in CosmeticEntitlement.__table__.c


def test_idempotent_regrant_contract_is_unique():
    names = {constraint.name for constraint in CosmeticEntitlement.__table__.constraints}
    assert "uq_cosmetic_entitlement_tenant_employee_product" in names


def test_presentation_values_match_w14_contract():
    from app.services.cosmetic_entitlement_service import COSMETIC_VALUES

    assert COSMETIC_VALUES["outfit"] == {"business", "casual", "technical", "formal"}
    assert COSMETIC_VALUES["accessory"] == {"none", "glasses", "headset", "badge"}


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

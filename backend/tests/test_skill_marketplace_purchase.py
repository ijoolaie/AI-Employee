from uuid import uuid4

from app.models.skill_marketplace_purchase import SkillMarketplacePurchase
from app.models.skill_package import EmployeeSkillInstallation
from app.models.skill_purchase_entitlement import SkillPurchaseEntitlement


def test_marketplace_purchase_has_buyer_employee_composite_fk():
    constraints = {
        tuple(column.name for column in fk.columns)
        for fk in SkillMarketplacePurchase.__table__.foreign_key_constraints
    }
    assert ("buyer_tenant_id", "employee_id") in constraints


def test_marketplace_purchase_has_seller_package_and_product_composite_fks():
    constraints = {
        tuple(column.name for column in fk.columns)
        for fk in SkillMarketplacePurchase.__table__.foreign_key_constraints
    }
    assert ("seller_tenant_id", "skill_package_id") in constraints
    assert ("seller_tenant_id", "product_id") in constraints


def test_installation_records_source_owner_tenant():
    assert hasattr(EmployeeSkillInstallation, "source_owner_tenant_id")


def test_entitlement_records_source_owner_and_publication():
    assert hasattr(SkillPurchaseEntitlement, "source_owner_tenant_id")
    assert hasattr(SkillPurchaseEntitlement, "source_publication_id")


def test_marketplace_purchase_model_has_idempotency_boundary():
    unique_sets = {
        frozenset(constraint.columns.keys())
        for constraint in SkillMarketplacePurchase.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert frozenset({"buyer_tenant_id", "idempotency_key"}) in unique_sets
    assert frozenset({"business_deal_id"}) in unique_sets

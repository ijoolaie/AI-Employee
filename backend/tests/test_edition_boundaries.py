from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.edition_lifecycle_service import (
    STATUS_ACTIVE,
    STATUS_DEPROVISIONED,
    STATUS_SUSPENDED,
    validate_deprovision_children,
    validate_transition,
)
from app.services.edition_service import (
    EDITION_CUSTOMER,
    EDITION_RESELLER,
    EDITION_VENDOR,
    assert_can_access,
    assert_direct_child,
)


def tenant(kind, parent=None):
    return SimpleNamespace(id=uuid4(), tenant_kind=kind, parent_tenant_id=getattr(parent, "id", None))


def test_vendor_can_access_direct_reseller_only():
    vendor = tenant(EDITION_VENDOR)
    reseller = tenant(EDITION_RESELLER, vendor)
    customer = tenant(EDITION_CUSTOMER, reseller)

    assert_can_access(vendor, reseller)
    with pytest.raises(HTTPException):
        assert_can_access(vendor, customer)


def test_reseller_can_access_direct_customers_but_not_vendor():
    vendor = tenant(EDITION_VENDOR)
    reseller = tenant(EDITION_RESELLER, vendor)
    customer = tenant(EDITION_CUSTOMER, reseller)

    assert_can_access(reseller, customer)
    with pytest.raises(HTTPException):
        assert_can_access(reseller, vendor)


def test_customer_cannot_cross_tenant_boundary():
    reseller = tenant(EDITION_RESELLER)
    customer = tenant(EDITION_CUSTOMER, reseller)
    sibling = tenant(EDITION_CUSTOMER, reseller)

    assert_can_access(customer, customer)
    with pytest.raises(HTTPException):
        assert_can_access(customer, reseller)
    with pytest.raises(HTTPException):
        assert_can_access(customer, sibling)


def test_child_kind_and_parent_are_both_required():
    vendor = tenant(EDITION_VENDOR)
    reseller = tenant(EDITION_RESELLER, vendor)
    customer = tenant(EDITION_CUSTOMER, reseller)

    assert_direct_child(vendor, reseller, EDITION_RESELLER)
    assert_direct_child(reseller, customer, EDITION_CUSTOMER)
    with pytest.raises(HTTPException):
        assert_direct_child(vendor, customer, EDITION_CUSTOMER)


def test_active_tenant_can_suspend_or_deprovision():
    validate_transition(STATUS_ACTIVE, STATUS_SUSPENDED)
    validate_transition(STATUS_ACTIVE, STATUS_DEPROVISIONED)


def test_suspended_tenant_can_resume_or_deprovision():
    validate_transition(STATUS_SUSPENDED, STATUS_ACTIVE)
    validate_transition(STATUS_SUSPENDED, STATUS_DEPROVISIONED)


def test_deprovisioned_tenant_cannot_be_reactivated():
    with pytest.raises(HTTPException):
        validate_transition(STATUS_DEPROVISIONED, STATUS_ACTIVE)
    with pytest.raises(HTTPException):
        validate_transition(STATUS_DEPROVISIONED, STATUS_SUSPENDED)


def test_deprovision_requires_all_children_to_be_deprovisioned():
    validate_deprovision_children([SimpleNamespace(status=STATUS_DEPROVISIONED)])
    with pytest.raises(HTTPException):
        validate_deprovision_children([SimpleNamespace(status=STATUS_ACTIVE)])
    with pytest.raises(HTTPException):
        validate_deprovision_children([SimpleNamespace(status=STATUS_SUSPENDED)])

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
    assert_release_identity,
)


def tenant(kind, parent=None):
    return SimpleNamespace(id=uuid4(), tenant_kind=kind, parent_tenant_id=getattr(parent, "id", None))


def test_vendor_can_access_direct_resellers_and_direct_customers_only():
    vendor = tenant(EDITION_VENDOR)
    reseller = tenant(EDITION_RESELLER, vendor)
    reseller_customer = tenant(EDITION_CUSTOMER, reseller)
    direct_customer = tenant(EDITION_CUSTOMER, vendor)

    assert_can_access(vendor, reseller)
    assert_can_access(vendor, direct_customer)
    with pytest.raises(HTTPException):
        assert_can_access(vendor, reseller_customer)



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

    direct_customer = tenant(EDITION_CUSTOMER, vendor)
    assert_direct_child(vendor, reseller, EDITION_RESELLER)
    assert_direct_child(vendor, direct_customer, EDITION_CUSTOMER)
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


def test_child_release_identity_must_match_parent():
    vendor = tenant(EDITION_VENDOR)
    vendor.vendor_release_tag = "v1.4.10"

    assert_release_identity(vendor, None)
    assert_release_identity(vendor, "v1.4.10")
    with pytest.raises(HTTPException):
        assert_release_identity(vendor, "v1.4.9")



def test_legacy_reseller_admin_routes_are_removed():
    from app.api.v1.router import api_router

    routes = [getattr(route, "path", "") for route in api_router.routes]
    assert not any(path.startswith("/reseller-admin") for path in routes)

def test_vendor_license_hierarchy_accepts_direct_customer_and_rejects_invalid_edges():
    from app.services.license_service import _valid_vendor_hierarchy_edge

    assert _valid_vendor_hierarchy_edge(EDITION_CUSTOMER, EDITION_VENDOR)
    assert _valid_vendor_hierarchy_edge(EDITION_CUSTOMER, EDITION_RESELLER)
    assert _valid_vendor_hierarchy_edge(EDITION_RESELLER, EDITION_VENDOR)
    assert not _valid_vendor_hierarchy_edge(EDITION_RESELLER, EDITION_RESELLER)
    assert not _valid_vendor_hierarchy_edge(EDITION_CUSTOMER, EDITION_CUSTOMER)

def test_vendor_direct_customer_routes_are_registered():
    from app.api.v1.edition_control import router as edition_router

    paths = {getattr(route, "path", "") for route in edition_router.routes}
    assert "/edition/vendor/customers" in paths
    assert "/edition/vendor/customers/{customer_id}/suspend" in paths
    assert "/edition/vendor/customers/{customer_id}/resume" in paths
    assert "/edition/vendor/customers/{customer_id}/deprovision" in paths
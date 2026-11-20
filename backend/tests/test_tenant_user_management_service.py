from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.tenant_user_management_service import _validate_actor, _validate_target


def tenant(kind, parent=None, status="active"):
    return SimpleNamespace(id=uuid4(), tenant_kind=kind, parent_tenant_id=getattr(parent, "id", None), status=status)


def test_vendor_can_manage_direct_reseller_direct_customer_and_nested_customer():
    vendor = tenant("vendor")
    reseller = tenant("reseller", vendor)
    direct_customer = tenant("customer", vendor)
    nested_customer = tenant("customer", reseller)
    _validate_actor(vendor, None)
    _validate_target(vendor, reseller, vendor, None)
    _validate_target(vendor, direct_customer, vendor, None)
    _validate_target(vendor, nested_customer, reseller, vendor)


def test_reseller_can_manage_only_direct_customer():
    vendor = tenant("vendor")
    reseller = tenant("reseller", vendor)
    customer = tenant("customer", reseller)
    sibling_reseller = tenant("reseller", vendor)
    sibling_customer = tenant("customer", sibling_reseller)
    _validate_actor(reseller, vendor)
    _validate_target(reseller, customer, reseller, vendor)
    with pytest.raises(HTTPException):
        _validate_target(reseller, sibling_customer, reseller, vendor)


@pytest.mark.parametrize("bad_actor", [
    lambda: tenant("vendor", tenant("vendor")),
    lambda: tenant("reseller"),
    lambda: tenant("customer"),
    lambda: tenant("vendor", status="suspended"),
])
def test_malformed_or_inactive_actor_hierarchy_is_rejected(bad_actor):
    actor = bad_actor()
    parent = None
    if actor.parent_tenant_id:
        parent = tenant("vendor")
        parent.id = actor.parent_tenant_id
    with pytest.raises(HTTPException):
        _validate_actor(actor, parent)


def test_sibling_vendor_foreign_ancestry_and_inactive_targets_are_rejected():
    vendor = tenant("vendor")
    sibling_vendor = tenant("vendor")
    foreign_reseller = tenant("reseller", sibling_vendor)
    inactive_customer = tenant("customer", vendor, status="suspended")
    _validate_actor(vendor, None)
    for target, parent, grandparent in (
        (foreign_reseller, sibling_vendor, None),
        (inactive_customer, vendor, None),
    ):
        with pytest.raises(HTTPException):
            _validate_target(vendor, target, parent, grandparent)


def test_nested_customer_requires_valid_reseller_to_vendor_chain():
    vendor = tenant("vendor")
    malformed_reseller = tenant("reseller", tenant("reseller"))
    customer = tenant("customer", malformed_reseller)
    with pytest.raises(HTTPException):
        _validate_target(vendor, customer, malformed_reseller, None)




@pytest.mark.parametrize("role_name,permission_code", [
    ("Employee Reader", "platform.admin"),
    ("Employee Reader", "vendor.reseller.create"),
    ("Platform Admin", "employee.read"),
    ("Superuser", "employee.read"),
])
def test_vendor_role_delegation_rejects_platform_and_control_plane_authority(role_name, permission_code):
    from app.api.v1.vendor_tenant_users import _assert_vendor_assignable_roles

    tenant_id = uuid4()
    ctx = SimpleNamespace(
        tenant_id=tenant_id,
        user=SimpleNamespace(roles=[SimpleNamespace(
            tenant_id=tenant_id,
            permissions=[SimpleNamespace(code="employee.read"), SimpleNamespace(code="vendor.reseller.manage")],
        )]),
    )
    role = SimpleNamespace(name=role_name, permissions=[SimpleNamespace(code=permission_code)])
    with pytest.raises(HTTPException) as exc:
        _assert_vendor_assignable_roles(ctx, [role])
    assert exc.value.status_code == 403


def test_vendor_role_delegation_allows_only_permissions_within_actor_authority():
    from app.api.v1.vendor_tenant_users import _assert_vendor_assignable_roles

    tenant_id = uuid4()
    ctx = SimpleNamespace(tenant_id=tenant_id, user=SimpleNamespace(roles=[SimpleNamespace(
        tenant_id=tenant_id, permissions=[SimpleNamespace(code="employee.read")],
    )]))
    role = SimpleNamespace(name="Employee Reader", permissions=[SimpleNamespace(code="employee.read")])
    _assert_vendor_assignable_roles(ctx, [role])

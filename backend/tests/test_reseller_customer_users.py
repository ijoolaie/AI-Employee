"""Unit tests for Reseller-managed direct Customer users."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import reseller_customer_users as customer_users


@pytest.mark.asyncio
async def test_customer_user_routes_reject_non_direct_child():
    reseller_id = uuid4()
    customer_id = uuid4()
    ctx = SimpleNamespace(
        tenant_id=reseller_id,
        tenant=SimpleNamespace(id=reseller_id, tenant_kind="reseller"),
        user_id=uuid4(),
    )
    customer = SimpleNamespace(
        id=customer_id,
        parent_tenant_id=uuid4(),
        tenant_kind="customer",
        status="active",
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: customer))
    )

    with pytest.raises(HTTPException) as exc:
        await customer_users._load_direct_customer(customer_id, ctx, db)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_customer_user_routes_reject_inactive_direct_child():
    reseller_id = uuid4()
    customer_id = uuid4()
    ctx = SimpleNamespace(
        tenant_id=reseller_id,
        tenant=SimpleNamespace(id=reseller_id, tenant_kind="reseller"),
        user_id=uuid4(),
    )
    customer = SimpleNamespace(
        id=customer_id,
        parent_tenant_id=reseller_id,
        tenant_kind="customer",
        status="suspended",
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: customer))
    )

    with pytest.raises(HTTPException) as exc:
        await customer_users._load_direct_customer(customer_id, ctx, db)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_customer_user_routes_accept_only_active_direct_child():
    reseller_id = uuid4()
    customer_id = uuid4()
    ctx = SimpleNamespace(
        tenant_id=reseller_id,
        tenant=SimpleNamespace(id=reseller_id, tenant_kind="reseller"),
        user_id=uuid4(),
    )
    customer = SimpleNamespace(
        id=customer_id,
        parent_tenant_id=reseller_id,
        tenant_kind="customer",
        status="active",
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: customer))
    )

    assert await customer_users._load_direct_customer(customer_id, ctx, db) is customer


def test_reseller_managed_member_role_is_an_explicit_customer_only_allowlist():
    assert "billing.manage" not in customer_users.CUSTOMER_MEMBER_PERMISSIONS
    assert "employee.delete" not in customer_users.CUSTOMER_MEMBER_PERMISSIONS
    assert "vendor.customer.create" not in customer_users.CUSTOMER_MEMBER_PERMISSIONS
    assert "reseller.customer.manage" not in customer_users.CUSTOMER_MEMBER_PERMISSIONS
    assert "employee.read" in customer_users.CUSTOMER_MEMBER_PERMISSIONS
    assert "workflow.execute" in customer_users.CUSTOMER_MEMBER_PERMISSIONS
    assert "workflow.write" not in customer_users.CUSTOMER_MEMBER_PERMISSIONS


def test_reseller_customer_user_routes_are_registered():
    routes = {
        (method, route.path)
        for route in customer_users.router.routes
        for method in (route.methods or set())
    }
    prefix = "/edition/reseller/customers/{customer_id}/users"
    assert ("GET", prefix) in routes
    assert ("POST", f"{prefix}/invitations") in routes
    assert ("POST", f"{prefix}/invitations/{{invitation_id}}/revoke") in routes
    assert ("POST", f"{prefix}/{{user_id}}/status") in routes

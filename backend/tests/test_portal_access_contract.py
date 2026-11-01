"""Server-side edition checks remain stricter than portal navigation labels."""

import ast
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.edition_service import (
    EDITION_CUSTOMER,
    EDITION_RESELLER,
    EDITION_VENDOR,
    require_edition,
)


def context(kind: str, *, is_superuser: bool = False):
    tenant_id = uuid4()
    tenant = SimpleNamespace(tenant_kind=kind, id=tenant_id)
    admin_role = SimpleNamespace(tenant_id=tenant_id, name="Admin")
    return SimpleNamespace(
        tenant=tenant,
        tenant_id=tenant_id,
        user=SimpleNamespace(is_superuser=is_superuser, roles=[admin_role]),
    )


@pytest.mark.parametrize(
    ("account_kind", "requested_edition", "allowed"),
    [
        (EDITION_VENDOR, EDITION_VENDOR, True),
        (EDITION_VENDOR, EDITION_RESELLER, False),
        (EDITION_VENDOR, EDITION_CUSTOMER, False),
        (EDITION_RESELLER, EDITION_VENDOR, False),
        (EDITION_RESELLER, EDITION_RESELLER, True),
        (EDITION_RESELLER, EDITION_CUSTOMER, False),
        (EDITION_CUSTOMER, EDITION_VENDOR, False),
        (EDITION_CUSTOMER, EDITION_RESELLER, False),
        (EDITION_CUSTOMER, EDITION_CUSTOMER, True),
    ],
)
def test_backend_edition_apis_stay_tenant_kind_scoped(
    account_kind: str, requested_edition: str, allowed: bool
):
    ctx = context(account_kind)
    if allowed:
        assert require_edition(ctx, requested_edition) is None
    else:
        with pytest.raises(HTTPException) as exc:
            require_edition(ctx, requested_edition)
        assert exc.value.status_code == 403


def test_portal_navigation_does_not_grant_platform_superuser_access():
    # The frontend may offer a portal entry point to a vendor, but this backend
    # policy still rejects any attempt to use a different edition's API.
    ctx = context(EDITION_VENDOR, is_superuser=False)
    with pytest.raises(HTTPException) as exc:
        require_edition(ctx, EDITION_CUSTOMER)
    assert exc.value.status_code == 403

def test_self_service_registration_does_not_create_a_platform_superuser():
    source_path = Path(__file__).parents[1] / "app" / "services" / "auth_service.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    registration = next(
        node for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "register_tenant_and_user"
    )
    user_constructors = [
        node for node in ast.walk(registration)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "User"
    ]
    assert user_constructors, "registration must explicitly construct its tenant user"
    superuser_values = {
        keyword.arg: keyword.value
        for constructor in user_constructors
        for keyword in constructor.keywords
        if keyword.arg == "is_superuser"
    }
    assert isinstance(superuser_values.get("is_superuser"), ast.Constant)
    assert superuser_values["is_superuser"].value is False

@pytest.mark.parametrize("account_kind", [EDITION_VENDOR, EDITION_RESELLER, EDITION_CUSTOMER])
def test_legacy_superuser_flag_cannot_bypass_edition_kind(account_kind: str):
    """Legacy global Core bypass must not cross commercial edition boundaries."""
    for requested_edition in {EDITION_VENDOR, EDITION_RESELLER, EDITION_CUSTOMER} - {account_kind}:
        with pytest.raises(HTTPException) as exc:
            require_edition(context(account_kind, is_superuser=True), requested_edition)
        assert exc.value.status_code == 403


def test_child_tenant_provisioning_does_not_create_a_platform_superuser():
    source_path = Path(__file__).parents[1] / "app" / "services" / "edition_service.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    provisioning = next(
        node for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "provision_child_tenant"
    )
    constructors = [
        node for node in ast.walk(provisioning)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "User"
    ]
    assert constructors, "child provisioning must explicitly construct its tenant user"
    values = {
        keyword.arg: keyword.value
        for constructor in constructors
        for keyword in constructor.keywords
        if keyword.arg == "is_superuser"
    }
    assert isinstance(values.get("is_superuser"), ast.Constant)
    assert values["is_superuser"].value is False

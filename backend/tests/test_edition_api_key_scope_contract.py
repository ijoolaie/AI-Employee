from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.edition_deps import (
    EDITION_RESELLER,
    EDITION_VENDOR,
    _enforce_api_key_scope,
)


def request(method: str, path: str):
    return SimpleNamespace(
        method=method,
        scope={"route": SimpleNamespace(path=path)},
    )


@pytest.mark.parametrize(
    ("kind", "path"),
    [
        (EDITION_VENDOR, "/api/v1/edition/licenses/vendor"),
        (EDITION_RESELLER, "/api/v1/edition/licenses/reseller"),
    ],
)
def test_license_list_requires_explicit_read_scope(kind: str, path: str):
    ctx = SimpleNamespace(
        api_key_id="api-key-id",
        api_key_scopes=["edition.licenses.read"],
    )
    assert _enforce_api_key_scope(ctx, request("GET", path), kind) is None


@pytest.mark.parametrize(
    ("kind", "path"),
    [
        (EDITION_VENDOR, "/api/v1/edition/licenses/vendor"),
        (EDITION_RESELLER, "/api/v1/edition/licenses/reseller"),
    ],
)
def test_license_list_rejects_api_key_without_read_scope(kind: str, path: str):
    ctx = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=["edition.licenses.issue"])
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(ctx, request("GET", path), kind)
    assert exc.value.status_code == 403


def test_license_list_rejects_legacy_api_key_without_scopes():
    ctx = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=None)
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(
            ctx,
            request("GET", "/api/v1/edition/licenses/vendor"),
            EDITION_VENDOR,
        )
    assert exc.value.status_code == 403

@pytest.mark.parametrize(
    ("kind", "path", "required_scope"),
    [
        (EDITION_VENDOR, f"/api/v1/edition/vendor/resellers/{{reseller_id}}/suspend", "edition.vendor.resellers.manage"),
        (EDITION_VENDOR, f"/api/v1/edition/vendor/resellers/{{reseller_id}}/resume", "edition.vendor.resellers.manage"),
        (EDITION_VENDOR, f"/api/v1/edition/vendor/resellers/{{reseller_id}}/deprovision", "edition.vendor.resellers.manage"),
        (EDITION_VENDOR, f"/api/v1/edition/vendor/customers/{{customer_id}}/suspend", "edition.vendor.customers.manage"),
        (EDITION_VENDOR, f"/api/v1/edition/vendor/customers/{{customer_id}}/resume", "edition.vendor.customers.manage"),
        (EDITION_VENDOR, f"/api/v1/edition/vendor/customers/{{customer_id}}/deprovision", "edition.vendor.customers.manage"),
        (EDITION_RESELLER, f"/api/v1/edition/reseller/customers/{{customer_id}}/suspend", "edition.reseller.customers.manage"),
        (EDITION_RESELLER, f"/api/v1/edition/reseller/customers/{{customer_id}}/resume", "edition.reseller.customers.manage"),
        (EDITION_RESELLER, f"/api/v1/edition/reseller/customers/{{customer_id}}/deprovision", "edition.reseller.customers.manage"),
    ],
)
def test_child_tenant_lifecycle_api_key_scope_contract(kind: str, path: str, required_scope: str):
    from app.core.edition_deps import EDITION_ROUTE_SCOPES, EDITION_SCOPE_ALLOWLIST_BY_KIND

    route_template = path.replace("/api/v1", "")
    assert EDITION_ROUTE_SCOPES[("POST", route_template)] == required_scope
    assert required_scope in EDITION_SCOPE_ALLOWLIST_BY_KIND[kind]

    authorized = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=[required_scope])
    assert _enforce_api_key_scope(authorized, request("POST", path), kind) is None

    unauthorized = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=["edition.licenses.read"])
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(unauthorized, request("POST", path), kind)
    assert exc.value.status_code == 403
    assert required_scope in exc.value.detail


def test_bearer_context_does_not_require_api_key_lifecycle_scope():
    ctx = SimpleNamespace(api_key_id=None, api_key_scopes=None)
    assert _enforce_api_key_scope(
        ctx,
        request("POST", "/api/v1/edition/reseller/customers/{customer_id}/deprovision"),
        EDITION_RESELLER,
    ) is None

@pytest.mark.parametrize("suffix", [
    "/edition/vendor/tenants/{target_tenant_id}/users",
    "/edition/vendor/tenants/{target_tenant_id}/users/roles",
])
def test_vendor_descendant_user_read_routes_require_dedicated_api_key_scope(suffix: str):
    from app.core.edition_deps import EDITION_ROUTE_SCOPES, EDITION_SCOPE_ALLOWLIST_BY_KIND

    scope = "edition.vendor.users.read"
    assert EDITION_ROUTE_SCOPES[("GET", suffix)] == scope
    assert scope in EDITION_SCOPE_ALLOWLIST_BY_KIND[EDITION_VENDOR]
    authorized = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=[scope])
    assert _enforce_api_key_scope(authorized, request("GET", f"/api/v1{suffix}"), EDITION_VENDOR) is None
    denied = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=["edition.vendor.tenants.read"])
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(denied, request("GET", f"/api/v1{suffix}"), EDITION_VENDOR)
    assert exc.value.status_code == 403


@pytest.mark.parametrize("method,path", [
    ("POST", "/edition/vendor/tenants/{target_tenant_id}/users/invitations"),
    ("POST", "/edition/vendor/tenants/{target_tenant_id}/users/invitations/{invitation_id}/revoke"),
    ("POST", "/edition/vendor/tenants/{target_tenant_id}/users/{user_id}/status"),
    ("POST", "/edition/vendor/tenants/{target_tenant_id}/users/{user_id}/roles"),
])
def test_vendor_descendant_user_write_routes_require_dedicated_api_key_scope(method: str, path: str):
    from app.core.edition_deps import EDITION_ROUTE_SCOPES, EDITION_SCOPE_ALLOWLIST_BY_KIND

    scope = "edition.vendor.users.manage"
    assert EDITION_ROUTE_SCOPES[(method, path)] == scope
    assert scope in EDITION_SCOPE_ALLOWLIST_BY_KIND[EDITION_VENDOR]
    authorized = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=[scope])
    assert _enforce_api_key_scope(authorized, request(method, f"/api/v1{path}"), EDITION_VENDOR) is None
    denied = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=["edition.vendor.users.read"])
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(denied, request(method, f"/api/v1{path}"), EDITION_VENDOR)
    assert exc.value.status_code == 403

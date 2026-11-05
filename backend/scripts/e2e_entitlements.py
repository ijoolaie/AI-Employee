"""Reusable real-stack registration and operator Demo-entitlement fixture."""
from __future__ import annotations

import json
from e2e_platform_admin_fixture import credentials as platform_admin_credentials
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def _call(base_url: str, method: str, path: str, payload: dict | None = None, token: str | None = None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None if payload is None else json.dumps(payload).encode()
    try:
        with urlopen(Request(base_url + path, data=body, headers=headers, method=method), timeout=20) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}



_PLATFORM_ADMIN_TOKEN: str | None = None

def ci_platform_admin_token(base_url: str) -> str:
    global _PLATFORM_ADMIN_TOKEN
    if _PLATFORM_ADMIN_TOKEN:
        return _PLATFORM_ADMIN_TOKEN
    email, password = platform_admin_credentials()
    status, login = _call(base_url, "POST", "/auth/login", {
        "tenant_slug": "ci-default-vendor", "email": email, "password": password,
    })
    assert status == 200, f"CI platform-admin login failed: {status}: {login}"
    _PLATFORM_ADMIN_TOKEN = (login.get("data") or {}).get("access_token")
    assert _PLATFORM_ADMIN_TOKEN, login
    return _PLATFORM_ADMIN_TOKEN

def entitle_existing_tenant(base_url: str, tenant_slug: str, email: str, password: str, *, reason: str = "Isolated real-stack E2E entitlement fixture"):
    status, login = _call(base_url, "POST", "/auth/login", {
        "tenant_slug": tenant_slug, "email": email, "password": password,
    })
    assert status == 200, f"restricted billing login failed: {status}: {login}"
    token = (login.get("data") or {}).get("access_token")
    assert token
    status, identity = _call(base_url, "GET", "/auth/me", token=token)
    assert status == 200, identity
    tenant = (identity.get("data") or {}).get("tenant") or {}
    assert tenant.get("access_granted") is False, tenant
    tenant_id = tenant.get("id")
    admin_token = ci_platform_admin_token(base_url)
    grant_status, grant = _call(base_url, "POST", f"/admin/tenants/{tenant_id}/demo-grants", {
        "reason": reason, "expires_in_days": 7,
    }, admin_token)
    assert grant_status == 201, grant
    status, identity = _call(base_url, "GET", "/auth/me", token=token)
    assert status == 200 and (identity.get("data") or {}).get("tenant", {}).get("access_granted") is True, identity
    return token, identity


def register_and_grant(base_url: str, payload: dict, *, reason: str = "Isolated real-stack E2E entitlement fixture"):
    status, registration = _call(base_url, "POST", "/auth/register", payload)
    assert status == 202, f"registration expected 202, got {status}: {registration}"
    login_payload = {
        "tenant_slug": payload["tenant_slug"],
        "email": payload["email"],
        "password": payload["password"],
    }
    status, login = _call(base_url, "POST", "/auth/login", login_payload)
    assert status == 200, f"restricted billing login failed: {status}: {login}"
    token = (login.get("data") or {}).get("access_token")
    assert token, f"login returned no access token: {login}"
    status, identity = _call(base_url, "GET", "/auth/me", token=token)
    assert status == 200, f"pending identity failed: {status}: {identity}"
    tenant = (identity.get("data") or {}).get("tenant") or {}
    assert tenant.get("access_granted") is False, f"new tenant was unexpectedly entitled: {tenant}"
    tenant_id = tenant.get("id")
    assert tenant_id, f"identity did not return tenant id: {identity}"

    admin_token = ci_platform_admin_token(base_url)
    status, grant = _call(base_url, "POST", f"/admin/tenants/{tenant_id}/demo-grants", {
        "reason": reason,
        "expires_in_days": 7,
    }, admin_token)
    assert status == 201, f"operator Demo grant failed: {status}: {grant}"
    status, identity = _call(base_url, "GET", "/auth/me", token=token)
    assert status == 200 and (identity.get("data") or {}).get("tenant", {}).get("access_granted") is True, identity
    user_id = (identity.get("data") or {}).get("user", {}).get("id")
    return tenant_id, user_id, token, identity

"""Real-stack P0 authentication certification.

Runs against the API inside the Compose stack and exercises the complete
register -> login -> current-user -> refresh -> current-user flow. The check
fails closed: every HTTP status, response envelope, token, and tenant/user
identity is validated.
"""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode())
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        raise AssertionError(f"{method} {path} returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    tenant_slug = f"cert-auth-{suffix}"
    email = f"cert-auth-{suffix}@example.com"
    password = "CertAuth-P0-2026!"

    status, registered = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"Certification Auth {suffix}",
            "tenant_slug": tenant_slug,
            "email": email,
            "password": password,
            "full_name": "P0 Certification User",
        },
    )
    assert status == 201, f"register status={status}"
    assert registered.get("success") is True, registered
    register_data = registered.get("data") or {}
    assert register_data.get("access_token"), "register did not return access_token"
    assert register_data.get("refresh_token"), "register did not return refresh_token"
    print("AUTH REGISTER PASS")

    status, logged_in = request(
        "POST",
        "/auth/login",
        {"email": email, "password": password, "tenant_slug": tenant_slug},
    )
    assert status == 200, f"login status={status}"
    assert logged_in.get("success") is True, logged_in
    login_data = logged_in.get("data") or {}
    access_token = login_data.get("access_token")
    refresh_token = login_data.get("refresh_token")
    assert access_token and refresh_token, "login did not return both tokens"
    assert login_data.get("token_type") == "bearer", login_data
    print("AUTH LOGIN PASS")

    status, me = request("GET", "/auth/me", token=access_token)
    assert status == 200, f"me status={status}"
    assert me.get("success") is True, me
    me_data = me.get("data") or {}
    assert me_data.get("user", {}).get("email") == email, me_data
    assert me_data.get("tenant", {}).get("slug") == tenant_slug, me_data
    assert me_data.get("user", {}).get("tenant_id") == me_data.get("tenant", {}).get("id"), me_data
    print("AUTH CURRENT-USER PASS")

    status, refreshed = request("POST", "/auth/refresh", {"refresh_token": refresh_token})
    assert status == 200, f"refresh status={status}"
    assert refreshed.get("success") is True, refreshed
    refresh_data = refreshed.get("data") or {}
    refreshed_access = refresh_data.get("access_token")
    refreshed_refresh = refresh_data.get("refresh_token")
    assert refreshed_access and refreshed_refresh, "refresh did not return both tokens"
    print("AUTH REFRESH PASS")

    status, refreshed_me = request("GET", "/auth/me", token=refreshed_access)
    assert status == 200, f"refreshed me status={status}"
    refreshed_data = refreshed_me.get("data") or {}
    assert refreshed_data.get("user", {}).get("email") == email, refreshed_data
    assert refreshed_data.get("tenant", {}).get("slug") == tenant_slug, refreshed_data
    print("AUTH CURRENT-USER AFTER REFRESH PASS")

    print("AUTH P0 REAL-STACK CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"AUTH P0 CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

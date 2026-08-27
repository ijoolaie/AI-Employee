"""Real-stack Product Acceptance certification for Developer/API-key and Admin boundaries."""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"raw": raw}
        return exc.code, body
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    email = f"i.joolaie+admin-dev-{suffix}@gmail.com"
    password = "CertAdminDev-2026!"

    status, registered = request("POST", "/auth/register", {
        "tenant_name": f"Admin Developer {suffix}",
        "tenant_slug": f"cert-admin-dev-{suffix}",
        "email": email,
        "password": password,
        "full_name": "Admin Developer User",
    })
    assert status == 201, registered
    token = (registered.get("data") or {}).get("access_token")
    assert token, registered

    status, denied = request("GET", "/admin/dashboard", token=token)
    assert status == 403, denied
    print("ADMIN NON-PLATFORM DENY PASS")

    key_name = f"cert-key-{suffix}"
    # Superusers must provide an explicit scope snapshot; omitting scopes is
    # intentionally rejected by the API to avoid ambiguous privilege grants.
    status, created = request("POST", "/api-keys", {"name": key_name, "scopes": ["employee.read"]}, token=token)
    assert status == 201, created
    created_data = created.get("data") or {}
    secret = created_data.get("key")
    key_id = created_data.get("id")
    assert secret and key_id, created
    assert secret.startswith("aiep_"), created
    assert created_data.get("scopes") == ["employee.read"], created
    print("DEVELOPER API KEY CREATE PASS")

    status, listed = request("GET", "/api-keys", token=token)
    assert status == 200, listed
    keys = listed.get("data") or []
    row = next((item for item in keys if item.get("id") == key_id), None)
    assert row is not None, listed
    assert "key" not in row and "secret" not in row, listed
    assert row.get("scopes") == ["employee.read"], listed
    print("DEVELOPER API KEY SECRET REDACTION PASS")

    status, revoked = request("POST", f"/api-keys/{key_id}/revoke", token=token)
    assert status == 200, revoked
    assert (revoked.get("data") or {}).get("revoked_at"), revoked
    print("DEVELOPER API KEY REVOKE PASS")

    status, listed_after = request("GET", "/api-keys", token=token)
    assert status == 200, listed_after
    row_after = next((item for item in (listed_after.get("data") or []) if item.get("id") == key_id), None)
    assert row_after and row_after.get("revoked_at"), listed_after
    print("PRODUCT ACCEPTANCE ADMIN / DEVELOPER PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PRODUCT ACCEPTANCE ADMIN / DEVELOPER FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

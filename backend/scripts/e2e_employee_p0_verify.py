"""Real-stack P0 Employee certification.

Exercises tenant-scoped employee creation, listing, retrieval, and version
publishing against the running Compose API.
"""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None):
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
        return exc.code, detail
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    tenant_slug = f"cert-employee-{suffix}"
    email = "i.joolaie@gmail.com"
    password = "CertEmployee-P0-2026!"

    status, registered = request("POST", "/auth/register", {
        "tenant_name": f"Certification Employee {suffix}",
        "tenant_slug": tenant_slug,
        "email": email,
        "password": password,
        "full_name": "Employee P0 Certification User",
    })
    assert status == 201, f"register: expected 201, got {status}: {registered}"
    data = registered.get("data") or {}
    token = data.get("access_token")
    assert token, f"register missing access_token: {registered}"
    print("EMPLOYEE AUTH PASS")

    slug = f"cert-employee-{suffix}"
    status, created = request("POST", "/employees", {
        "slug": slug,
        "name": "Certification Employee",
        "kind": "custom",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "prompt_template": "Certification employee",
        "allowed_tools": [],
        "rules": {},
    }, token)
    assert status == 201, f"create employee: expected 201, got {status}: {created}"
    employee = created.get("data") or {}
    employee_id = employee.get("id")
    assert employee_id, f"create employee missing id: {created}"
    assert employee.get("slug") == slug, created
    print("EMPLOYEE CREATE PASS")

    status, listed = request("GET", "/employees", token=token)
    assert status == 200, f"list employees: expected 200, got {status}: {listed}"
    employees = (listed.get("data") or [])
    assert any(str(item.get("id")) == str(employee_id) for item in employees), listed
    print("EMPLOYEE LIST PASS")

    status, fetched = request("GET", f"/employees/{employee_id}", token=token)
    assert status == 200, f"get employee: expected 200, got {status}: {fetched}"
    fetched_data = fetched.get("data") or {}
    assert str(fetched_data.get("id")) == str(employee_id), fetched
    assert fetched_data.get("slug") == slug, fetched
    print("EMPLOYEE GET PASS")

    status, versioned = request("POST", f"/employees/{employee_id}/versions", {
        "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}}},
        "output_schema": {"type": "object"},
        "prompt_template": "Certification employee v2",
        "allowed_tools": [],
        "rules": {"certification": True},
    }, token)
    assert status == 201, f"publish version: expected 201, got {status}: {versioned}"
    version = versioned.get("data") or {}
    assert version.get("version_number") == 2, versioned
    assert version.get("is_current") is True, versioned
    print("EMPLOYEE VERSION PASS")

    print("EMPLOYEE P0 REAL-STACK CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"EMPLOYEE P0 CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

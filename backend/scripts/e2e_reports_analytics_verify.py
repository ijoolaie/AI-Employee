"""Real-stack tenant-isolation certification for Reports / Analytics sources.

The customer Reports page is an aggregate of tenant-scoped Dashboard, Usage,
and Runs data. This gate creates two independent tenants, writes a resource
only to tenant A, and verifies that tenant B cannot observe that signal.
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
        with urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        raise AssertionError(f"{method} {path} returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def register_tenant(suffix: str, label: str) -> str:
    slug = f"cert-reports-{label.lower()}-{suffix}"
    email = f"cert-reports-{label.lower()}-{suffix}@example.invalid"
    status, response = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"Reports Certification {label} {suffix}",
            "tenant_slug": slug,
            "email": email,
            "password": "CertReports-2026!",
            "full_name": f"Reports Certification {label}",
        },
    )
    assert status == 201, f"{label} registration expected 201, got {status}: {response}"
    token = (response.get("data") or {}).get("access_token")
    assert token, f"{label} registration missing access token: {response}"
    print(f"REPORTS TENANT {label} REGISTER PASS")
    return token


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    token_a = register_tenant(suffix, "A")
    token_b = register_tenant(suffix, "B")

    employee_payload = {
        "slug": f"cert-reports-employee-{suffix}",
        "name": "Reports Isolation Employee",
        "kind": "custom",
        "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]},
        "output_schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}},
        "prompt_template": "Reports isolation certification: {{task}}",
        "allowed_tools": [],
        "rules": {},
    }
    status, created = request("POST", "/employees", employee_payload, token_a)
    assert status == 201, f"tenant A employee create expected 201, got {status}: {created}"
    employee_id = (created.get("data") or {}).get("id")
    assert employee_id, f"tenant A employee create missing id: {created}"
    print("REPORTS TENANT A SEED RESOURCE PASS")

    status, dashboard_a = request("GET", "/customer-dashboard", token=token_a)
    assert status == 200, f"tenant A dashboard expected 200, got {status}: {dashboard_a}"
    data_a = dashboard_a.get("data") or {}
    assert data_a.get("employee_count", 0) >= 1, data_a
    print("REPORTS TENANT A DASHBOARD SEES OWN RESOURCE PASS")

    status, dashboard_b = request("GET", "/customer-dashboard", token=token_b)
    assert status == 200, f"tenant B dashboard expected 200, got {status}: {dashboard_b}"
    data_b = dashboard_b.get("data") or {}
    assert data_b.get("employee_count", 0) == 0, data_b
    assert employee_id not in {str(item.get("id")) for item in data_b.get("recent_runs", [])}, data_b
    print("REPORTS TENANT B DASHBOARD ISOLATION PASS")

    status, usage_a = request("GET", "/usage/summary", token=token_a)
    assert status == 200, f"tenant A usage expected 200, got {status}: {usage_a}"
    usage_data_a = usage_a.get("data") or {}
    assert isinstance(usage_data_a, dict), usage_a
    print("REPORTS TENANT A USAGE SUMMARY PASS")

    status, usage_b = request("GET", "/usage/summary", token=token_b)
    assert status == 200, f"tenant B usage expected 200, got {status}: {usage_b}"
    usage_data_b = usage_b.get("data") or {}
    assert isinstance(usage_data_b, dict), usage_b
    print("REPORTS TENANT B USAGE SUMMARY ISOLATION PASS")

    status, runs_a = request("GET", "/runs", token=token_a)
    assert status == 200, f"tenant A runs expected 200, got {status}: {runs_a}"
    ids_a = {str(item.get("id")) for item in (runs_a.get("data") or [])}

    status, runs_b = request("GET", "/runs", token=token_b)
    assert status == 200, f"tenant B runs expected 200, got {status}: {runs_b}"
    ids_b = {str(item.get("id")) for item in (runs_b.get("data") or [])}
    assert ids_a.isdisjoint(ids_b), f"cross-tenant run leakage: A={ids_a}, B={ids_b}"
    print("REPORTS RUN LIST TENANT ISOLATION PASS")

    print("REPORTS / ANALYTICS TENANT ISOLATION REAL-STACK CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"REPORTS / ANALYTICS CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

"""Real-stack Product Acceptance certification for Employee -> Run -> AI -> Result."""
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
    tenant_slug = f"cert-product-{suffix}"
    email = "i.joolaie@gmail.com"
    password = "CertProduct-2026!"

    status, registered = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"Product Acceptance {suffix}",
            "tenant_slug": tenant_slug,
            "email": email,
            "password": password,
            "full_name": "Product Acceptance User",
        },
    )
    assert status == 201, f"registration expected 201, got {status}: {registered}"
    access_token = (registered.get("data") or {}).get("access_token")
    assert access_token, f"registration did not return access token: {registered}"
    print("PRODUCT ACCEPTANCE AUTH PASS")

    employee_payload = {
        "slug": f"cert-employee-{suffix}",
        "name": "Product Acceptance Employee",
        "kind": "custom",
        "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]},
        "output_schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}},
        "prompt_template": "Complete the certification task: {{task}}",
        "allowed_tools": [],
        "rules": {},
    }
    status, created = request("POST", "/employees", employee_payload, access_token)
    assert status == 201, f"employee create expected 201, got {status}: {created}"
    employee = (created.get("data") or {})
    employee_id = employee.get("id")
    assert employee_id, f"employee create missing id: {created}"
    assert employee.get("slug") == employee_payload["slug"], created
    print("PRODUCT ACCEPTANCE EMPLOYEE CREATE PASS")

    version_payload = {
        "input_schema": employee_payload["input_schema"],
        "output_schema": employee_payload["output_schema"],
        "prompt_template": employee_payload["prompt_template"],
        "allowed_tools": [],
        "rules": {},
    }
    status, versioned = request("POST", f"/employees/{employee_id}/versions", version_payload, access_token)
    assert status == 201, f"employee version expected 201, got {status}: {versioned}"
    version = versioned.get("data") or {}
    assert version.get("version_number") == 2, f"expected published version 2: {versioned}"
    assert version.get("is_current") is True, versioned
    print("PRODUCT ACCEPTANCE EMPLOYEE VERSION PASS")

    status, listed = request("GET", "/employees", token=access_token)
    assert status == 200, f"employee list expected 200, got {status}: {listed}"
    assert any(item.get("id") == employee_id for item in (listed.get("data") or [])), listed

    status, fetched = request("GET", f"/employees/{employee_id}", token=access_token)
    assert status == 200, f"employee get expected 200, got {status}: {fetched}"
    assert (fetched.get("data") or {}).get("id") == employee_id, fetched
    print("PRODUCT ACCEPTANCE EMPLOYEE LIST/GET PASS")

    status, run_created = request(
        "POST",
        "/runs",
        {"employee_id": employee_id, "input_data": {"task": "return a deterministic acceptance result"}},
        access_token,
    )
    assert status == 201, f"run creation expected 201, got {status}: {run_created}"
    run = run_created.get("data") or {}
    run_id = run.get("id")
    assert run_id, f"run creation missing id: {run_created}"
    assert run.get("status") in {"pending", "running", "success"}, run_created
    print("PRODUCT ACCEPTANCE RUN CREATE PASS")

    deadline = time.time() + 45
    terminal = None
    while time.time() < deadline:
        status, current = request("GET", f"/runs/{run_id}", token=access_token)
        assert status == 200, f"run get expected 200, got {status}: {current}"
        terminal = current.get("data") or {}
        if terminal.get("status") in {"success", "failed", "cancelled"}:
            break
        time.sleep(2)

    assert terminal is not None, "run polling returned no state"
    assert terminal.get("status") == "success", f"run did not succeed: {terminal}"
    output = terminal.get("output_data") or {}
    assert isinstance(output.get("text"), str) and "Deterministic certification result" in output["text"], terminal
    assert terminal.get("completed_at"), terminal
    assert terminal.get("total_tokens", 0) > 0, terminal
    print("PRODUCT ACCEPTANCE RUN TERMINAL RESULT PASS")
    print("PRODUCT ACCEPTANCE EMPLOYEE -> RUN -> AI -> RESULT PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PRODUCT ACCEPTANCE CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

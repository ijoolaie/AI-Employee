"""Real-stack Product Acceptance gate for Workflow -> Approval -> Schedule."""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None):
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
        return exc.code, detail
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def expect(status: int, expected: int, label: str, body: dict) -> dict:
    assert status == expected, f"{label}: expected HTTP {expected}, got {status}: {body}"
    return body.get("data") or {}


def register(suffix: str):
    email = f"i.joolaie+workflow-{suffix}@gmail.com"
    tenant_slug = f"cert-workflow-{suffix}"
    status, body = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"Workflow Acceptance {suffix}",
            "tenant_slug": tenant_slug,
            "email": email,
            "password": "CertWorkflow-P0-2026!",
            "full_name": "Workflow Acceptance Admin",
        },
    )
    data = expect(status, 201, "workflow certification registration", body)
    token = data.get("access_token")
    assert token, body
    return token


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    token = register(suffix)

    workflow_payload = {
        "slug": f"cert-workflow-approval-{suffix}",
        "name": "P0 Workflow Approval Certification",
        "trigger_type": "manual",
        "steps": [
            {
                "key": "human_gate",
                "type": "approval",
                "message": "Approve the Product Acceptance workflow gate.",
                "timeout_seconds": 300,
            }
        ],
    }
    status, body = request("POST", "/workflows", workflow_payload, token)
    workflow = expect(status, 201, "workflow creation", body)
    workflow_id = workflow["id"]
    print(f"WORKFLOW CREATE PASS workflow={workflow_id}")

    status, body = request("GET", f"/workflows/{workflow_id}", token=token)
    current = expect(status, 200, "workflow read", body)
    assert current["id"] == workflow_id
    assert current.get("current_version_id"), current
    print("WORKFLOW READ/VERSION PASS")

    status, body = request(
        "POST",
        f"/workflows/{workflow_id}/runs",
        {"input_data": {"certification": "workflow-approval-schedule"}, "idempotency_key": f"cert-{suffix}"},
        token,
    )
    run = expect(status, 201, "workflow run creation", body)
    run_id = run["id"]
    print(f"WORKFLOW RUN CREATE PASS run={run_id}")

    approval = None
    deadline = time.time() + 45
    while time.time() < deadline:
        query = urlencode({"status_filter": "pending"})
        status, body = request("GET", f"/workflow-approvals?{query}", token=token)
        approvals = expect(status, 200, "pending approval list", body)
        approval = next((item for item in approvals if item.get("workflow_run_id") == run_id), None)
        if approval:
            break
        time.sleep(2)
    assert approval, "workflow run did not create a pending human approval"
    approval_id = approval["id"]
    print(f"APPROVAL CREATED PASS approval={approval_id}")

    status, body = request(
        "POST",
        f"/workflow-approvals/{approval_id}/decision",
        {"decision": "approve", "reason": "Product Acceptance approval gate passed."},
        token,
    )
    decided = expect(status, 200, "approval decision", body)
    assert decided.get("status") == "approved", decided
    print("APPROVAL APPROVE PASS")

    final_run = None
    deadline = time.time() + 45
    while time.time() < deadline:
        status, body = request("GET", f"/workflows/{workflow_id}/runs/{run_id}", token=token)
        final_run = expect(status, 200, "workflow run status", body)
        if final_run.get("status") in {"completed", "failed", "cancelled"}:
            break
        time.sleep(2)
    assert final_run and final_run.get("status") == "completed", final_run
    print("WORKFLOW RESUME/COMPLETE PASS")

    status, body = request(
        "POST",
        f"/workflows/{workflow_id}/schedules",
        {"cron_expression": "0 0 * * *", "timezone": "UTC"},
        token,
    )
    schedule = expect(status, 201, "schedule creation", body)
    schedule_id = schedule["id"]
    assert schedule.get("is_active") is True
    assert schedule.get("next_run_at"), schedule
    print(f"SCHEDULE CREATE/NEXT-RUN PASS schedule={schedule_id}")

    status, body = request("GET", f"/workflows/{workflow_id}/schedules", token=token)
    schedules = expect(status, 200, "schedule list", body)
    assert any(item.get("id") == schedule_id for item in schedules), schedules
    print("SCHEDULE TENANT-SCOPED READ PASS")

    status, body = request(
        "PATCH",
        f"/workflow-schedules/{schedule_id}",
        {"is_active": False},
        token,
    )
    updated = expect(status, 200, "schedule deactivate", body)
    assert updated.get("is_active") is False and updated.get("next_run_at") is None, updated
    print("SCHEDULE UPDATE/DEACTIVATE PASS")

    status, body = request("DELETE", f"/workflow-schedules/{schedule_id}", token=token)
    deleted = expect(status, 200, "schedule delete", body)
    assert deleted.get("deleted") is True, deleted
    print("SCHEDULE DELETE PASS")

    print("WORKFLOW + APPROVAL + SCHEDULE PRODUCT ACCEPTANCE CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"WORKFLOW/APPROVAL/SCHEDULE CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

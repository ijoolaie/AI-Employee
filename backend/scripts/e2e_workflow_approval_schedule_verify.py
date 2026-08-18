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
    status, body = request("POST", "/auth/register", {"tenant_name": f"Workflow Acceptance {suffix}", "tenant_slug": f"cert-workflow-{suffix}", "email": email, "password": "CertWorkflow-P0-2026!", "full_name": "Workflow Acceptance Admin"})
    data = expect(status, 201, "workflow registration", body)
    assert data.get("access_token"), data
    return data["access_token"]


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    token = register(suffix)
    status, body = request("POST", "/workflows", {"slug": f"cert-workflow-{suffix}", "name": "P0 Workflow Approval Certification", "trigger_type": "manual", "steps": [{"key": "human_gate", "type": "approval", "message": "Approve certification gate.", "timeout_seconds": 300}]}, token)
    workflow = expect(status, 201, "workflow creation", body)
    workflow_id = workflow["id"]
    print("WORKFLOW CREATE PASS")

    status, body = request("GET", f"/workflows/{workflow_id}", token=token)
    current = expect(status, 200, "workflow read", body)
    assert current.get("current_version_id"), current
    print("WORKFLOW VERSION PASS")

    status, body = request("POST", f"/workflows/{workflow_id}/runs", {"input_data": {"certification": "workflow-approval-schedule"}, "idempotency_key": f"cert-{suffix}"}, token)
    run = expect(status, 201, "workflow run", body)
    run_id = run["id"]
    deadline = time.time() + 45
    approval = None
    while time.time() < deadline:
        status, body = request("GET", f"/workflow-approvals?{urlencode({'status_filter': 'pending'})}", token=token)
        approvals = expect(status, 200, "pending approvals", body)
        approval = next((item for item in approvals if item.get("workflow_run_id") == run_id), None)
        if approval:
            break
        time.sleep(2)
    assert approval, "pending approval was not created"
    print("APPROVAL CREATE PASS")

    status, body = request("POST", f"/workflow-approvals/{approval['id']}/decision", {"decision": "approve", "reason": "Certification approval"}, token)
    decided = expect(status, 200, "approval decision", body)
    assert decided.get("status") == "approved", decided
    print("APPROVAL APPROVE PASS")

    deadline = time.time() + 45
    final = None
    while time.time() < deadline:
        status, body = request("GET", f"/workflows/{workflow_id}/runs/{run_id}", token=token)
        final = expect(status, 200, "workflow run status", body)
        if final.get("status") in {"completed", "success", "failed", "cancelled", "error"}:
            break
        time.sleep(2)
    assert final and final.get("status") in {"completed", "success"}, final
    print("WORKFLOW RESUME COMPLETE PASS")

    status, body = request("POST", f"/workflows/{workflow_id}/schedules", {"cron_expression": "0 0 * * *", "timezone": "UTC"}, token)
    schedule = expect(status, 201, "schedule create", body)
    schedule_id = schedule["id"]
    assert schedule.get("is_active") and schedule.get("next_run_at"), schedule
    print("SCHEDULE CREATE NEXT-RUN PASS")

    status, body = request("GET", f"/workflows/{workflow_id}/schedules", token=token)
    schedules = expect(status, 200, "schedule list", body)
    assert any(item.get("id") == schedule_id for item in schedules), schedules
    print("SCHEDULE TENANT READ PASS")

    status, body = request("PATCH", f"/workflow-schedules/{schedule_id}", {"is_active": False}, token)
    updated = expect(status, 200, "schedule deactivate", body)
    assert updated.get("is_active") is False and updated.get("next_run_at") is None, updated
    print("SCHEDULE DEACTIVATE PASS")

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

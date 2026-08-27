"""Real-stack certification for Workflow -> Employee -> Run -> Result."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.services import edition_service, license_service

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


async def provision_certification_license(tenant_id: uuid.UUID, suffix: str) -> None:
    """Provision the same Vendor -> Reseller -> Customer license boundary used in production."""
    async with AsyncSessionLocal() as db:
        customer = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
        if customer is None:
            raise AssertionError(f"Certification tenant not found: {tenant_id}")

        customer.tenant_kind = edition_service.EDITION_CUSTOMER
        vendor = Tenant(
            name=f"Certification Vendor {suffix}",
            slug=f"cert-vendor-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_VENDOR,
            settings={"certification_fixture": True},
        )
        db.add(vendor)
        await db.flush()

        reseller = Tenant(
            name=f"Certification Reseller {suffix}",
            slug=f"cert-reseller-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_RESELLER,
            parent_tenant_id=vendor.id,
            settings={"certification_fixture": True},
        )
        db.add(reseller)
        await db.flush()

        customer.parent_tenant_id = reseller.id
        customer.vendor_release_tag = "v1.2.0"
        customer.delivery_revision = "production-certification"
        await db.flush()

        license_row = await license_service.issue_license(
            db,
            issuer=reseller,
            tenant=customer,
            feature_codes=["employee.run"],
            metadata={
                "certification_fixture": True,
                "purpose": "workflow-employee-certification",
                "vendor_tenant_id": str(vendor.id),
            },
        )
        assert license_row.status == "active"
        assert "employee.run" in (license_row.feature_codes or [])
        await db.commit()


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    status, registered = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"Workflow Employee Acceptance {suffix}",
            "tenant_slug": f"cert-workflow-employee-{suffix}",
            "email": f"i.joolaie+workflow-{suffix}@gmail.com",
            "password": "CertWorkflowEmployee-2026!",
            "full_name": "Workflow Employee Acceptance User",
        },
    )
    assert status == 201, registered
    token = (registered.get("data") or {}).get("access_token")
    assert token

    status, me = request("GET", "/auth/me", token=token)
    assert status == 200, me
    tenant_id = uuid.UUID(str(((me.get("data") or {}).get("tenant") or {}).get("id")))
    asyncio.run(provision_certification_license(tenant_id, suffix))
    print("WORKFLOW EMPLOYEE LICENSE FIXTURE PASS")

    employee_payload = {
        "slug": f"cert-workflow-employee-{suffix}",
        "name": "Workflow Employee Acceptance",
        "kind": "custom",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
        "output_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        "prompt_template": "Complete this certification task and return the requested result: {{task}}",
        "allowed_tools": [],
        "rules": {},
    }
    status, created = request("POST", "/employees", employee_payload, token)
    assert status == 201, created
    employee_id = (created.get("data") or {}).get("id")
    assert employee_id

    status, versioned = request(
        "POST",
        f"/employees/{employee_id}/versions",
        {k: employee_payload[k] for k in ("input_schema", "output_schema", "prompt_template", "allowed_tools", "rules")},
        token,
    )
    assert status == 201, versioned
    assert (versioned.get("data") or {}).get("is_current") is True

    workflow_payload = {
        "slug": f"cert-workflow-{suffix}",
        "name": "Workflow Employee Acceptance",
        "trigger_type": "manual",
        "steps": [
            {
                "key": "process-message",
                "type": "employee",
                "employee_id": employee_id,
                "input_mapping": {"task": "$.input.task"},
                "output_key": "employee_result",
                "retry_max": 0,
                "timeout_seconds": 300,
            }
        ],
    }
    status, workflow_response = request("POST", "/workflows", workflow_payload, token)
    assert status == 201, workflow_response
    workflow_id = (workflow_response.get("data") or {}).get("id")
    assert workflow_id
    print("WORKFLOW CREATE + MAPPING PASS")

    status, run_response = request(
        "POST",
        f"/workflows/{workflow_id}/runs",
        {
            "input_data": {"task": "return a deterministic certification result"},
            "idempotency_key": f"workflow-employee-{suffix}",
        },
        token,
    )
    assert status == 201, run_response
    run_id = (run_response.get("data") or {}).get("id")
    assert run_id
    print("WORKFLOW RUN CREATE PASS")

    deadline = time.time() + 60
    final = None
    while time.time() < deadline:
        status, current = request("GET", f"/workflows/{workflow_id}/runs/{run_id}", token=token)
        assert status == 200, current
        final = current.get("data") or {}
        if final.get("status") in {"success", "completed", "failed", "cancelled", "timed_out"}:
            break
        time.sleep(2)

    assert final and final.get("status") in {"success", "completed"}, final
    context = final.get("context") or {}
    result = (context.get("steps") or {}).get("process-message") or {}
    assert isinstance(result.get("text"), str) and result["text"], final
    assert final.get("completed_at"), final
    print("WORKFLOW EMPLOYEE TERMINAL RESULT PASS")
    print("WORKFLOW -> EMPLOYEE -> RUN -> RESULT PRODUCT ACCEPTANCE PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"WORKFLOW EMPLOYEE CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

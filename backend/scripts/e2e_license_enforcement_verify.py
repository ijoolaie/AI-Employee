"""Real-stack certification for commercial license enforcement at Run creation."""
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
        return exc.code, detail
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


async def provision_fixture(tenant_id: uuid.UUID, suffix: str) -> tuple[uuid.UUID, uuid.UUID]:
    async with AsyncSessionLocal() as db:
        customer = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
        assert customer is not None, f"tenant not found: {tenant_id}"
        customer.tenant_kind = edition_service.EDITION_CUSTOMER
        vendor = Tenant(name=f"License Certification Vendor {suffix}", slug=f"lic-cert-vendor-{suffix}", status="active", tenant_kind=edition_service.EDITION_VENDOR, settings={"certification_fixture": True})
        db.add(vendor)
        await db.flush()
        reseller = Tenant(name=f"License Certification Reseller {suffix}", slug=f"lic-cert-reseller-{suffix}", status="active", tenant_kind=edition_service.EDITION_RESELLER, parent_tenant_id=vendor.id, settings={"certification_fixture": True})
        db.add(reseller)
        await db.flush()
        customer.parent_tenant_id = reseller.id
        customer.vendor_release_tag = "v1.2.1"
        customer.delivery_revision = "license-enforcement-certification"
        await db.commit()
        return vendor.id, reseller.id


async def issue_license(issuer_id: uuid.UUID, customer_id: uuid.UUID, features: list[str]) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        issuer = (await db.execute(select(Tenant).where(Tenant.id == issuer_id))).scalar_one()
        customer = (await db.execute(select(Tenant).where(Tenant.id == customer_id))).scalar_one()
        row = await license_service.issue_license(db, issuer=issuer, tenant=customer, feature_codes=features, metadata={"certification_fixture": True})
        await db.commit()
        return row.id


async def revoke_license(issuer_id: uuid.UUID, license_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        issuer = (await db.execute(select(Tenant).where(Tenant.id == issuer_id))).scalar_one()
        await license_service.revoke_license(db, issuer=issuer, license_id=license_id, reason="production certification")
        await db.commit()


def expect_rejected(status: int, payload: dict, label: str) -> None:
    assert status == 409, f"{label}: expected HTTP 409, got {status}: {payload}"
    detail = json.dumps(payload, sort_keys=True).lower()
    assert "license" in detail or "authorized features" in detail, f"{label}: unexpected rejection: {payload}"
    print(f"{label} PASS")


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    status, registered = request("POST", "/auth/register", {"tenant_name": f"License Certification {suffix}", "tenant_slug": f"license-cert-{suffix}", "email": f"license-cert-{suffix}@example.com", "password": "LicenseCert-2026!", "full_name": "License Certification User"})
    assert status == 201, registered
    token = (registered.get("data") or {}).get("access_token")
    assert token, registered
    print("LICENSE ENFORCEMENT AUTH PASS")

    status, me = request("GET", "/auth/me", token=token)
    assert status == 200, me
    tenant_id = uuid.UUID(str(((me.get("data") or {}).get("tenant") or {}).get("id")))
    _, reseller_id = asyncio.run(provision_fixture(tenant_id, suffix))
    print("LICENSE ENFORCEMENT EDITION FIXTURE PASS")

    employee_payload = {"slug": f"license-cert-employee-{suffix}", "name": "License Certification Employee", "kind": "custom", "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]}, "output_schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}}, "prompt_template": "Complete the task: {{task}}", "allowed_tools": [], "rules": {}}
    status, created = request("POST", "/employees", employee_payload, token)
    assert status == 201, created
    employee_id = (created.get("data") or {}).get("id")
    assert employee_id, created
    print("LICENSE ENFORCEMENT EMPLOYEE CREATE PASS")

    run_payload = {"employee_id": employee_id, "input_data": {"task": "license enforcement certification"}}
    status, payload = request("POST", "/runs", run_payload, token)
    expect_rejected(status, payload, "LICENSE MISSING RUN REJECT")

    wrong_license_id = asyncio.run(issue_license(reseller_id, tenant_id, ["tool:send_email"]))
    status, payload = request("POST", "/runs", run_payload, token)
    expect_rejected(status, payload, "LICENSE WRONG-FEATURE RUN REJECT")
    asyncio.run(revoke_license(reseller_id, wrong_license_id))

    valid_license_id = asyncio.run(issue_license(reseller_id, tenant_id, ["employee.run"]))
    status, payload = request("POST", "/runs", run_payload, token)
    assert status == 201, f"LICENSE VALID RUN ALLOW failed: {payload}"
    run_id = (payload.get("data") or {}).get("id")
    assert run_id, payload
    print("LICENSE VALID RUN ALLOW PASS")

    deadline = time.time() + 45
    terminal = None
    while time.time() < deadline:
        status, current = request("GET", f"/runs/{run_id}", token=token)
        assert status == 200, current
        terminal = current.get("data") or {}
        if terminal.get("status") in {"success", "failed", "cancelled"}:
            break
        time.sleep(2)
    assert terminal and terminal.get("status") == "success", terminal
    print("LICENSE VALID RUN EXECUTION PASS")

    asyncio.run(revoke_license(reseller_id, valid_license_id))
    status, payload = request("POST", "/runs", run_payload, token)
    expect_rejected(status, payload, "LICENSE REVOKED RUN REJECT")
    print("COMMERCIAL LICENSE ENFORCEMENT P0 REAL-STACK CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"COMMERCIAL LICENSE ENFORCEMENT CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

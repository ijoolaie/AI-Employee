"""Real-stack Product Acceptance certification for Employee -> Run -> AI -> Result."""
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
    """Create a real, feature-scoped commercial license for this ephemeral gate tenant.

    The production edition hierarchy is Vendor -> Reseller -> Customer.  The
    certification fixture must exercise that same boundary: the registered
    customer becomes a direct child of a certification reseller, while that
    reseller is a direct child of a certification vendor.  The reseller then
    issues the customer license through the normal production service.
    """
    async with AsyncSessionLocal() as db:
        customer = (
            await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        ).scalar_one_or_none()
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
        customer.vendor_release_tag = "v1.2.1"
        customer.delivery_revision = "production-certification"
        await db.flush()
        await db.refresh(customer)
        await db.refresh(reseller)
        await db.refresh(vendor)

        if (
            reseller.parent_tenant_id != vendor.id
            or reseller.tenant_kind != edition_service.EDITION_RESELLER
            or customer.parent_tenant_id != reseller.id
            or customer.tenant_kind != edition_service.EDITION_CUSTOMER
        ):
            raise AssertionError(
                "Certification edition fixture is invalid: "
                f"vendor={vendor.id}, reseller={reseller.id}, customer={customer.id}, "
                f"reseller_parent={reseller.parent_tenant_id}, "
                f"customer_parent={customer.parent_tenant_id}, "
                f"reseller_kind={reseller.tenant_kind!r}, "
                f"customer_kind={customer.tenant_kind!r}"
            )

        license_row = await license_service.issue_license(
            db,
            issuer=reseller,
            tenant=customer,
            feature_codes=["employee.run"],
            metadata={
                "certification_fixture": True,
                "purpose": "production-certification",
                "vendor_tenant_id": str(vendor.id),
            },
        )
        assert license_row.status == "active", license_row
        assert "employee.run" in (license_row.feature_codes or []), license_row
        await db.commit()


def _parse_deterministic_result(text: str) -> dict:
    """Parse the provider's fenced JSON result and return its semantic payload."""
    normalized = text.strip()
    if normalized.startswith("```"):
        lines = normalized.splitlines()
        if lines and lines[0].strip().lower() in {"```json", "```"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        normalized = "\n".join(lines).strip()
    try:
        value = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"deterministic acceptance output is not valid JSON: {text!r}"
        ) from exc
    if not isinstance(value, dict):
        raise AssertionError(f"deterministic acceptance output must be a JSON object: {value!r}")
    return value


def _assert_deterministic_contract(text: str, terminal: dict) -> None:
    """Accept known deterministic provider contracts without prose coupling.

    The acceptance gate validates semantic meaning rather than one provider's
    exact wording. Supported contracts are:
      * legacy flat: accepted/deterministic_success/confirmation
      * nested: Completed + acceptance=true + Absolute + ACCEPTED
      * current flat: status=success + result=true
    """
    result = _parse_deterministic_result(text)

    flat_contract = (
        result.get("status") == "accepted"
        and result.get("result") == "deterministic_success"
        and result.get("confirmation") is True
    )

    nested_result = result.get("result")
    nested_contract = (
        result.get("task_status") == "Completed"
        and isinstance(nested_result, dict)
        and nested_result.get("acceptance") is True
        and nested_result.get("determinism_level") == "Absolute"
        and nested_result.get("output_value") == "ACCEPTED"
    )

    current_flat_contract = (
        result.get("status") == "success"
        and result.get("result") is True
    )

    if not (flat_contract or nested_contract or current_flat_contract):
        raise AssertionError(
            "deterministic acceptance semantic contract mismatch: "
            f"parsed_output={result!r}; terminal={terminal!r}"
        )


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

    status, me = request("GET", "/auth/me", token=access_token)
    assert status == 200, f"auth me expected 200, got {status}: {me}"
    tenant_id_raw = ((me.get("data") or {}).get("tenant") or {}).get("id")
    assert tenant_id_raw, f"auth me missing tenant id: {me}"
    tenant_id = uuid.UUID(str(tenant_id_raw))
    asyncio.run(provision_certification_license(tenant_id, suffix))
    print("PRODUCT ACCEPTANCE COMMERCIAL LICENSE FIXTURE PASS")

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
    text = output.get("text")
    assert isinstance(text, str) and text.strip(), terminal

    _assert_deterministic_contract(text, terminal)
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

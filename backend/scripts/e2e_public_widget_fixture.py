"""Create a licensed disposable tenant and public widget for browser/API CI."""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.services import edition_service, license_service

BASE = os.getenv("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def call(method, path, data=None, token=None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(BASE + path, data=None if data is None else json.dumps(data).encode(), headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


async def provision_execution_license(tenant_id, suffix):
    """Use the same isolated vendor/reseller/customer license fixture as product E2E."""
    async with AsyncSessionLocal() as db:
        customer = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
        assert customer is not None, f"fixture tenant not found: {tenant_id}"
        customer.tenant_kind = edition_service.EDITION_CUSTOMER

        vendor = Tenant(
            name=f"Widget CI Vendor {suffix}",
            slug=f"widget-ci-vendor-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_VENDOR,
            settings={"certification_fixture": True},
        )
        db.add(vendor)
        await db.flush()

        reseller = Tenant(
            name=f"Widget CI Reseller {suffix}",
            slug=f"widget-ci-reseller-{suffix}",
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

        assert reseller.parent_tenant_id == vendor.id
        assert customer.parent_tenant_id == reseller.id
        license_row = await license_service.issue_license(
            db,
            issuer=reseller,
            tenant=customer,
            feature_codes=["employee.run"],
            metadata={
                "certification_fixture": True,
                "purpose": "public-widget-browser-api",
                "vendor_tenant_id": str(vendor.id),
            },
        )
        assert license_row.status == "active"
        assert "employee.run" in (license_row.feature_codes or [])
        await db.commit()


def main():
    suffix = uuid.uuid4().hex[:16]
    status, result = call("POST", "/auth/register", {
        "tenant_name": "Widget CI " + suffix,
        "tenant_slug": "widget-ci-" + suffix,
        "email": "widget-ci-" + suffix + "@example.com",
        "password": os.environ.get("CI_FIXTURE_PASSWORD", "ci-only-fixture-password-2026"),
        "full_name": "Widget CI Admin",
    })
    assert status == 201, result
    token = result["data"]["access_token"]

    status, identity = call("GET", "/auth/me", token=token)
    assert status == 200, identity
    tenant_id = uuid.UUID(identity["data"]["tenant"]["id"])
    asyncio.run(provision_execution_license(tenant_id, suffix))

    status, employee = call("POST", "/employees", {
        "slug": "widget-ci-" + suffix,
        "name": "CI Public Support Employee",
        "kind": "custom",
        "input_schema": {},
        "output_schema": {},
        "prompt_template": "Return the input unchanged.",
        "allowed_tools": [],
        "rules": {},
    }, token)
    assert status == 201, employee
    employee_id = employee["data"]["id"]
    for _ in range(10):
        status, _ = call("GET", "/employees/" + employee_id, token=token)
        if status == 200:
            break
        time.sleep(0.25)
    assert status == 200, "employee did not become visible"

    status, channel = call("POST", "/customer-channels", {
        "employee_id": employee_id,
        "name": "CI Public Widget",
        "channel_type": "web_widget",
        "config": {},
    }, token)
    assert status == 201, channel
    public_key = channel["data"]["public_key"]
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
        stream.write("PUBLIC_CHAT_KEY=" + public_key + "\n")
    print("Disposable licensed tenant, employee, and public channel provisioned.")


if __name__ == "__main__":
    main()

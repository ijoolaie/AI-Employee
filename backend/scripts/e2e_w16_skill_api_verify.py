"""Real-stack W16 employee skill API tenant-isolation and entitlement gate."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.product import Product
from app.models.skill_package import SkillPackage
from app.models.tenant import Tenant
from app.services import audit_service, edition_lifecycle_service, skill_marketplace_service

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def assert_status(actual: int, expected: int, label: str, body: dict) -> None:
    assert actual == expected, f"{label}: expected HTTP {expected}, got {actual}: {body}"


def register(suffix: str, label: str) -> tuple[str, str]:
    tenant_slug = f"w16-skill-api-{label}-{suffix}"
    status, response = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"W16 Skill API {label} Tenant {suffix}",
            "tenant_slug": tenant_slug,
            "email": f"w16-skill-api-{label}-{suffix}@example.com",
            "password": "W16SkillApiE2E-2026!",
            "full_name": f"W16 Skill API {label} Admin",
        },
    )
    assert_status(status, 201, f"{label} registration", response)
    token = (response.get("data") or {}).get("access_token")
    assert token, f"{label} registration did not return an access token"
    return tenant_slug, token


async def create_package(
    tenant_slug: str,
    *,
    product: bool = False,
) -> tuple[str, str, str | None]:
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))).scalar_one()
        employee = None
        if product:
            product_row = Product(
                tenant_id=tenant.id,
                sku=f"w16-skill-{tenant_slug}",
                name="W16 Commercial Skill",
                description="Entitlement-bound skill fixture",
                category="employee_skill",
                price=Decimal("10.00"),
                currency="EUR",
                inventory=10,
                attributes={
                    "skill_package_slug": "commercial-api-skill",
                    "skill_package_version": 1,
                },
                is_active=True,
            )
            db.add(product_row)
            await db.flush()
            package = await skill_marketplace_service.create_package(
                db,
                tenant_id=tenant.id,
                slug="commercial-api-skill",
                name="Commercial API Skill",
                version=1,
                product_id=product_row.id,
            )
            await skill_marketplace_service.publish_package(
                db,
                tenant_id=tenant.id,
                package_id=package.id,
                actor_id=tenant.id,
            )
            await db.commit()
            return str(tenant.id), str(package.id), str(product_row.id)

        package = await skill_marketplace_service.create_package(
            db,
            tenant_id=tenant.id,
            slug="free-api-skill",
            name="Free API Skill",
            version=1,
        )
        await skill_marketplace_service.publish_package(
            db,
            tenant_id=tenant.id,
            package_id=package.id,
            actor_id=tenant.id,
        )
        await db.commit()
        return str(tenant.id), str(package.id), None


async def cleanup(slugs: list[str]) -> None:
    if not slugs:
        return
    async with AsyncSessionLocal() as db:
        tenants = list((await db.execute(select(Tenant).where(Tenant.slug.in_(slugs)))).scalars().all())
        for tenant in tenants:
            if tenant.status != edition_lifecycle_service.STATUS_DEPROVISIONED:
                await edition_lifecycle_service.transition_tenant_status(
                    db,
                    tenant=tenant,
                    target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
                    actor_id=None,
                    audit_tenant_id=tenant.id,
                    audit_metadata={"certification_fixture": True, "cleanup_mode": "deprovision"},
                )
        await db.commit()


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    slugs: list[str] = []
    try:
        tenant_a, token_a = register(suffix, "a")
        tenant_b, token_b = register(suffix, "b")
        slugs.extend([tenant_a, tenant_b])

        status, employee_response = request(
            "POST",
            "/employees",
            {
                "slug": f"w16-skill-api-{suffix}",
                "name": "W16 Skill API Employee",
                "kind": "custom",
                "input_schema": {},
                "output_schema": {},
                "prompt_template": "Return the input unchanged.",
                "allowed_tools": [],
                "rules": {},
            },
            token=token_a,
        )
        assert_status(status, 201, "tenant A employee create", employee_response)
        employee_a = (employee_response.get("data") or {}).get("id")
        assert employee_a

        _, package_a, _ = asyncio.run(create_package(tenant_a))

        status, installed = request(
            "POST",
            f"/employees/{employee_a}/skills/{package_a}",
            token=token_a,
        )
        assert_status(status, 200, "same-tenant skill install", installed)
        installation_id = (installed.get("data") or {}).get("id")
        assert installation_id
        assert (installed.get("data") or {}).get("status") == "active"
        print("SAME-TENANT SKILL INSTALL PASS")

        status, listed = request("GET", f"/employees/{employee_a}/skills", token=token_a)
        assert_status(status, 200, "same-tenant skill list", listed)
        ids = {(item or {}).get("id") for item in (listed.get("data") or [])}
        assert installation_id in ids
        print("SAME-TENANT SKILL LIST PASS")

        status, cross_list = request("GET", f"/employees/{employee_a}/skills", token=token_b)
        assert_status(status, 404, "cross-tenant skill list", cross_list)
        print("CROSS-TENANT SKILL LIST REJECT PASS")

        status, cross_revoke = request(
            "DELETE",
            f"/employees/{employee_a}/skills/{package_a}",
            token=token_b,
        )
        assert_status(status, 404, "cross-tenant skill revoke", cross_revoke)
        print("CROSS-TENANT SKILL REVOKE REJECT PASS")

        status, revoked = request(
            "DELETE",
            f"/employees/{employee_a}/skills/{package_a}",
            token=token_a,
        )
        assert_status(status, 200, "same-tenant skill revoke", revoked)
        assert (revoked.get("data") or {}).get("status") == "revoked"
        print("SAME-TENANT SKILL REVOKE PASS")

        _, commercial_package, product_id = asyncio.run(create_package(tenant_a, product=True))
        assert product_id

        status, commercial = request(
            "POST",
            f"/employees/{employee_a}/skills/{commercial_package}",
            token=token_a,
        )
        assert_status(status, 422, "commercial skill without entitlement", commercial)
        assert "verified purchase entitlement" in str(commercial)
        print("COMMERCIAL SKILL FAIL-CLOSED WITHOUT ENTITLEMENT PASS")

        print("W16 EMPLOYEE SKILL API REAL-STACK TENANT + ENTITLEMENT GATE PASS")
        return 0
    finally:
        try:
            asyncio.run(cleanup(slugs))
        except Exception as exc:
            print(f"CERTIFICATION FIXTURE CLEANUP FAIL: {type(exc).__name__}", file=sys.stderr)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"W16 SKILL API REAL-STACK GATE FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

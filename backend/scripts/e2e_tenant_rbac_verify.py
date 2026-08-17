"""Real-stack P0 certification for tenant isolation and RBAC.

The check intentionally exercises the HTTP API against the running Compose
stack. A small database fixture is created only to model a real restricted
(non-superuser) tenant member; authorization itself is verified through HTTP
requests.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.role import Permission, Role, role_permissions, user_roles
from app.models.user import User


BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")
CERT_EMAIL_BASE = "i.joolaie@gmail.com"


def request(
    method: str,
    path: str,
    payload: dict | None = None,
    token: str | None = None,
) -> tuple[int, dict]:
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
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        return exc.code, detail
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def assert_status(actual: int, expected: int, label: str, body: dict) -> None:
    assert actual == expected, f"{label}: expected HTTP {expected}, got {actual}: {body}"


def register(suffix: str, label: str) -> tuple[str, str, str]:
    tenant_slug = f"cert-{label}-{suffix}"
    email = f"i.joolaie+gate2-{label}-{suffix}@gmail.com"
    password = "CertTenantRbac-P0-2026!"
    status, response = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"P0 {label} Tenant {suffix}",
            "tenant_slug": tenant_slug,
            "email": email,
            "password": password,
            "full_name": f"P0 {label} Admin",
        },
    )
    assert_status(status, 201, f"{label} registration", response)
    data = response.get("data") or {}
    token = data.get("access_token")
    assert token, f"{label} registration returned no access token"
    return tenant_slug, email, token


async def create_restricted_member(tenant_slug: str, suffix: str) -> tuple[str, str]:
    async with AsyncSessionLocal() as db:
        from app.models.tenant import Tenant

        tenant = (await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))).scalar_one()
        permission = (
            await db.execute(select(Permission).where(Permission.code == "employee.read"))
        ).scalar_one_or_none()
        if permission is None:
            permission = Permission(code="employee.read", description="Read employees")
            db.add(permission)
            await db.flush()

        role = (
            await db.execute(
                select(Role).where(Role.tenant_id == tenant.id, Role.name == "Certification Read Only")
            )
        ).scalar_one_or_none()
        if role is None:
            role = Role(
                tenant_id=tenant.id,
                name="Certification Read Only",
                description="P0 certification fixture: employee.read only",
            )
            db.add(role)
            await db.flush()
        await db.execute(
            insert(role_permissions)
            .values(role_id=role.id, permission_id=permission.id)
            .on_conflict_do_nothing()
        )

        email = f"i.joolaie+gate2-readonly-{suffix}@gmail.com"
        password = "CertTenantRbac-ReadOnly-2026!"
        member = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(password),
            full_name="P0 Restricted Member",
            is_active=True,
            is_superuser=False,
            is_platform_admin=False,
        )
        db.add(member)
        await db.flush()
        await db.execute(
            insert(user_roles)
            .values(user_id=member.id, role_id=role.id)
            .on_conflict_do_nothing()
        )
        await db.commit()
        return email, password


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    tenant_a_slug, _, token_a = register(suffix, "a")
    tenant_b_slug, _, token_b = register(suffix, "b")
    print(f"TENANT A REGISTER PASS tenant={tenant_a_slug}")
    print(f"TENANT B REGISTER PASS tenant={tenant_b_slug}")

    status, me_a = request("GET", "/auth/me", token=token_a)
    assert_status(status, 200, "tenant A current-user", me_a)
    me_a_data = me_a.get("data") or {}
    assert me_a_data.get("tenant", {}).get("slug") == tenant_a_slug, me_a_data
    assert me_a_data.get("user", {}).get("tenant_id") == me_a_data.get("tenant", {}).get("id"), me_a_data
    print("TENANT A CONTEXT PASS")

    status, created = request(
        "POST",
        "/employees",
        {
            "slug": f"p0-isolation-{suffix}",
            "name": "P0 Isolation Employee",
            "kind": "custom",
            "input_schema": {},
            "output_schema": {},
            "prompt_template": "Return the input unchanged.",
            "allowed_tools": [],
            "rules": {},
        },
        token=token_a,
    )
    assert_status(status, 201, "tenant A employee create", created)
    employee_id = (created.get("data") or {}).get("id")
    assert employee_id, created
    print(f"TENANT A EMPLOYEE CREATE PASS employee={employee_id}")

    status, cross_read = request("GET", f"/employees/{employee_id}", token=token_b)
    assert_status(status, 404, "cross-tenant employee read", cross_read)
    print("CROSS-TENANT READ REJECT PASS")

    status, cross_write = request(
        "POST",
        f"/employees/{employee_id}/versions",
        {
            "input_schema": {},
            "output_schema": {},
            "prompt_template": "cross-tenant write must fail",
            "allowed_tools": [],
            "rules": {},
        },
        token=token_b,
    )
    assert_status(status, 404, "cross-tenant employee write", cross_write)
    print("CROSS-TENANT WRITE REJECT PASS")

    restricted_email, restricted_password = asyncio.run(
        create_restricted_member(tenant_a_slug, suffix)
    )
    status, restricted_login = request(
        "POST",
        "/auth/login",
        {"email": restricted_email, "password": restricted_password, "tenant_slug": tenant_a_slug},
    )
    assert_status(status, 200, "restricted member login", restricted_login)
    restricted_token = (restricted_login.get("data") or {}).get("access_token")
    assert restricted_token, restricted_login
    print("RBAC RESTRICTED USER LOGIN PASS")

    status, allowed_read = request("GET", "/employees", token=restricted_token)
    assert_status(status, 200, "restricted employee read", allowed_read)
    print("RBAC ALLOWED READ PASS")

    status, denied_write = request(
        "POST",
        "/employees",
        {
            "slug": f"p0-rbac-denied-{suffix}",
            "name": "Must Not Be Created",
            "kind": "custom",
            "input_schema": {},
            "output_schema": {},
            "prompt_template": "This write must be denied.",
            "allowed_tools": [],
            "rules": {},
        },
        token=restricted_token,
    )
    assert_status(status, 403, "restricted employee write", denied_write)
    assert "Missing permission: employee.write" in str(denied_write), denied_write
    print("RBAC WRITE DENY PASS")

    print("TENANT ISOLATION + RBAC P0 REAL-STACK CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"TENANT/RBAC P0 CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

"""Real-stack P0 certification for tenant isolation and RBAC."""
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


def request(method: str, path: str, payload: dict | None = None, token: str | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode()
    request_headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=request_headers, method=method)
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


def request_multipart_file(token: str, filename: str, content: bytes, content_type: str = "text/plain") -> tuple[int, dict]:
    boundary = f"----AIEmployeeTenantIsolation{time.time_ns()}"
    body = (f"--{boundary}\r\n" f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n' f"Content-Type: {content_type}\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
    headers = {"Accept": "application/json", "Content-Type": f"multipart/form-data; boundary={boundary}", "Authorization": f"Bearer {token}"}
    req = Request(f"{BASE_URL}/files", data=body, headers=headers, method="POST")
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


def assert_status(actual: int, expected: int, label: str, body: dict) -> None:
    assert actual == expected, f"{label}: expected HTTP {expected}, got {actual}: {body}"


def register(suffix: str, label: str) -> tuple[str, str, str]:
    tenant_slug = f"cert-{label}-{suffix}"
    email = f"i.joolaie+gate2-{label}-{suffix}@gmail.com"
    password = "CertTenantRbac-P0-2026!"
    status, response = request("POST", "/auth/register", {"tenant_name": f"P0 {label} Tenant {suffix}", "tenant_slug": tenant_slug, "email": email, "password": password, "full_name": f"P0 {label} Admin"})
    assert_status(status, 201, f"{label} registration", response)
    token = (response.get("data") or {}).get("access_token")
    assert token, response
    return tenant_slug, email, token


async def create_restricted_member(tenant_slug: str, suffix: str) -> tuple[str, str]:
    async with AsyncSessionLocal() as db:
        from app.models.tenant import Tenant
        tenant = (await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))).scalar_one()
        permission = (await db.execute(select(Permission).where(Permission.code == "employee.read"))).scalar_one_or_none()
        if permission is None:
            permission = Permission(code="employee.read", description="Read employees")
            db.add(permission)
            await db.flush()
        role = (await db.execute(select(Role).where(Role.tenant_id == tenant.id, Role.name == "Certification Read Only"))).scalar_one_or_none()
        if role is None:
            role = Role(tenant_id=tenant.id, name="Certification Read Only", description="P0 certification fixture: employee.read only")
            db.add(role)
            await db.flush()
        await db.execute(insert(role_permissions).values(role_id=role.id, permission_id=permission.id).on_conflict_do_nothing())
        email = f"i.joolaie+gate2-readonly-{suffix}@gmail.com"
        password = "CertTenantRbac-ReadOnly-2026!"
        member = User(tenant_id=tenant.id, email=email, password_hash=hash_password(password), full_name="P0 Restricted Member", is_active=True, is_superuser=False, is_platform_admin=False)
        db.add(member)
        await db.flush()
        await db.execute(insert(user_roles).values(user_id=member.id, role_id=role.id).on_conflict_do_nothing())
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
    assert me_a_data.get("tenant", {}).get("slug") == tenant_a_slug
    assert me_a_data.get("user", {}).get("tenant_id") == me_a_data.get("tenant", {}).get("id")
    print("TENANT A CONTEXT PASS")

    status, created = request("POST", "/employees", {"slug": f"p0-isolation-{suffix}", "name": "P0 Isolation Employee", "kind": "custom", "input_schema": {}, "output_schema": {}, "prompt_template": "Return the input unchanged.", "allowed_tools": [], "rules": {}}, token=token_a)
    assert_status(status, 201, "tenant A employee create", created)
    employee_id = (created.get("data") or {}).get("id")
    assert employee_id
    print(f"TENANT A EMPLOYEE CREATE PASS employee={employee_id}")

    status, cross_read = request("GET", f"/employees/{employee_id}", token=token_b)
    assert_status(status, 404, "cross-tenant employee read", cross_read)
    print("CROSS-TENANT EMPLOYEE READ REJECT PASS")
    status, cross_write = request("POST", f"/employees/{employee_id}/versions", {"input_schema": {}, "output_schema": {}, "prompt_template": "cross-tenant write must fail", "allowed_tools": [], "rules": {}}, token=token_b)
    assert_status(status, 404, "cross-tenant employee write", cross_write)
    print("CROSS-TENANT EMPLOYEE WRITE REJECT PASS")

    file_status, file_response = request_multipart_file(token_a, filename=f"p0-tenant-a-{suffix}.txt", content=f"TENANT_A_ONLY_MARKER_{suffix}".encode())
    assert_status(file_status, 201, "tenant A file create", file_response)
    file_id = (file_response.get("data") or {}).get("id")
    assert file_id
    print(f"TENANT A FILE CREATE PASS file={file_id}")
    status, cross_file_read = request("GET", f"/files/{file_id}", token=token_b)
    assert_status(status, 404, "cross-tenant file read", cross_file_read)
    print("CROSS-TENANT FILE READ REJECT PASS")
    status, cross_file_download = request("GET", f"/files/{file_id}/download", token=token_b)
    assert_status(status, 404, "cross-tenant file download", cross_file_download)
    print("CROSS-TENANT FILE DOWNLOAD REJECT PASS")
    status, cross_file_delete = request("DELETE", f"/files/{file_id}", token=token_b)
    assert_status(status, 404, "cross-tenant file delete", cross_file_delete)
    print("CROSS-TENANT FILE DELETE REJECT PASS")
    status, allowed_file_read = request("GET", f"/files/{file_id}", token=token_a)
    assert_status(status, 200, "same-tenant file read", allowed_file_read)
    print("SAME-TENANT FILE READ PASS")

    restricted_email, restricted_password = asyncio.run(create_restricted_member(tenant_a_slug, suffix))
    status, restricted_login = request("POST", "/auth/login", {"email": restricted_email, "password": restricted_password, "tenant_slug": tenant_a_slug})
    assert_status(status, 200, "restricted member login", restricted_login)
    restricted_token = (restricted_login.get("data") or {}).get("access_token")
    assert restricted_token
    print("RBAC RESTRICTED USER LOGIN PASS")
    status, allowed_read = request("GET", "/employees", token=restricted_token)
    assert_status(status, 200, "restricted employee read", allowed_read)
    print("RBAC ALLOWED READ PASS")
    status, denied_write = request("POST", "/employees", {"slug": f"p0-rbac-denied-{suffix}", "name": "Must Not Be Created", "kind": "custom", "input_schema": {}, "output_schema": {}, "prompt_template": "This write must be denied.", "allowed_tools": [], "rules": {}}, token=restricted_token)
    assert_status(status, 403, "restricted employee write", denied_write)
    assert "Missing permission: employee.write" in str(denied_write)
    print("RBAC WRITE DENY PASS")

    # Knowledge isolation: Tenant A's file is the only source for its marker.
    # Tenant B must not be able to retrieve or index Tenant A's knowledge resource.
    status, cross_index = request("POST", f"/knowledge/index/{file_id}", token=token_b)
    assert_status(status, 404, "cross-tenant knowledge index", cross_index)
    print("CROSS-TENANT KNOWLEDGE INDEX REJECT PASS")

    status, search_b = request("POST", "/knowledge/search", {"query": f"TENANT_A_ONLY_MARKER_{suffix}", "limit": 10}, token=token_b)
    assert_status(status, 200, "tenant B knowledge search", search_b)
    search_data = search_b.get("data") or {}
    assert not search_data.get("results"), f"cross-tenant knowledge leakage: {search_data}"
    print("CROSS-TENANT KNOWLEDGE SEARCH ISOLATION PASS")

    print("TENANT ISOLATION + RBAC + KNOWLEDGE P0 REAL-STACK CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"TENANT/RBAC P0 CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

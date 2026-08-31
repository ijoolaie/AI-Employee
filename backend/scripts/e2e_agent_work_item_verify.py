"""Real-stack certification for Agent WorkItem -> runtime binding -> Run correlation."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal
from app.models.agent_definition import AgentDefinition
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services import edition_service, license_service

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, object]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else None
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
    """Provision the same real commercial license boundary used by product acceptance."""
    async with AsyncSessionLocal() as db:
        customer = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
        if customer is None:
            raise AssertionError(f"Certification tenant not found: {tenant_id}")

        customer.tenant_kind = edition_service.EDITION_CUSTOMER
        vendor = Tenant(
            name=f"Certification Vendor {suffix}",
            slug=f"cert-agent-vendor-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_VENDOR,
            settings={"certification_fixture": True},
        )
        db.add(vendor)
        await db.flush()
        reseller = Tenant(
            name=f"Certification Reseller {suffix}",
            slug=f"cert-agent-reseller-{suffix}",
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
        license_row = await license_service.issue_license(
            db,
            issuer=reseller,
            tenant=customer,
            feature_codes=["employee.run"],
            metadata={"certification_fixture": True, "purpose": "production-certification", "vendor_tenant_id": str(vendor.id)},
        )
        assert license_row.status == "active", license_row
        assert "employee.run" in (license_row.feature_codes or []), license_row
        await db.commit()


async def create_agent_stack(tenant_id: uuid.UUID, suffix: str) -> tuple[uuid.UUID, uuid.UUID]:
    async with AsyncSessionLocal() as db:
        employee = Employee(tenant_id=tenant_id, slug=f"cert-agent-employee-{suffix}", name="Agent Certification Employee", kind="custom", is_active=True)
        db.add(employee)
        await db.flush()
        version = EmployeeVersion(employee_id=employee.id, version_number=1, is_current=True, input_schema={}, output_schema={}, prompt_template="Deterministic Agent Certification", allowed_tools=[], rules={})
        definition = AgentDefinition(tenant_id=tenant_id, slug=f"cert-agent-definition-{suffix}", name="Agent Certification Definition", capabilities=["execution"], allowed_tools=[], model_policy={}, input_schema={}, output_schema={}, policy_requirements={}, enabled=True)
        db.add_all([version, definition])
        await db.flush()
        db.add(AgentRuntimeBinding(tenant_id=tenant_id, agent_definition_id=definition.id, employee_version_id=version.id, is_active=True))
        agent_id = uuid.uuid4()
        await db.execute(text("INSERT INTO agent_instances (id, tenant_id, agent_definition_id, name, configuration, status, max_concurrency, budget_policy, enabled) VALUES (:id, :tenant_id, :definition_id, :name, '{}'::jsonb, 'enabled', 1, '{}'::jsonb, true)"), {"id": agent_id, "tenant_id": tenant_id, "definition_id": definition.id, "name": "Agent Certification Instance"})
        await db.commit()
        return agent_id, version.id


async def create_agent_work_item(tenant_id: uuid.UUID, agent_id: uuid.UUID, suffix: str) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        item = WorkItem(tenant_id=tenant_id, title="Unified Agent WorkItem runtime acceptance", status=WorkItemStatus.READY, executor_type=ExecutorType.AGENT, executor_id=agent_id, input_data={"task": "deterministic agent execution acceptance"}, policy_context={}, idempotency_key=f"agent-unified-work-item-{suffix}")
        db.add(item)
        await db.commit()
        return item.id


async def verify_runtime(work_item_id: uuid.UUID, tenant_id: uuid.UUID, agent_id: uuid.UUID, version_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        item = await db.get(WorkItem, work_item_id)
        assert item is not None
        assert item.status is WorkItemStatus.RUNNING
        assert item.output_data and item.output_data["executor_type"] == "agent"
        assert item.output_data["agent_instance_id"] == str(agent_id)
        assert item.output_data["employee_version_id"] == str(version_id)
        run_id = uuid.UUID(str(item.output_data["run_id"]))
        run = await db.get(Run, run_id)
        assert run is not None
        assert run.tenant_id == tenant_id
        assert run.employee_version_id == version_id


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    status, registered = request("POST", "/auth/register", {"tenant_name": f"Agent WorkItem Acceptance {suffix}", "tenant_slug": f"cert-agent-work-item-{suffix}", "email": f"i.joolaie+agent-{suffix}@gmail.com", "password": "CertAgentWorkItem-2026!", "full_name": "Agent WorkItem Acceptance User"})
    assert status == 201, registered
    token = (registered.get("data") or {}).get("access_token")
    assert token
    status, me = request("GET", "/auth/me", token=token)
    assert status == 200, me
    tenant_id = uuid.UUID(str(((me.get("data") or {}).get("tenant") or {}).get("id")))
    asyncio.run(provision_certification_license(tenant_id, suffix))
    print("UNIFIED AGENT WORKITEM COMMERCIAL LICENSE FIXTURE PASS")
    agent_id, version_id = asyncio.run(create_agent_stack(tenant_id, suffix))
    work_item_id = asyncio.run(create_agent_work_item(tenant_id, agent_id, suffix))
    status, assigned = request("POST", f"/work-items/{work_item_id}/assign/agent", {"agent_instance_id": str(agent_id)}, token=token)
    assert status == 200, assigned
    assert assigned["status"] == "assigned"
    status, dispatched = request("POST", f"/work-items/{work_item_id}/dispatch", token=token)
    assert status == 200, dispatched
    assert dispatched["status"] == "running"
    assert dispatched["dispatched"] is True
    asyncio.run(verify_runtime(work_item_id, tenant_id, agent_id, version_id))
    status, history = request("GET", f"/work-items/{work_item_id}/history", token=token)
    assert status == 200, history
    actions = {entry["action"] for entry in history}
    assert "work_item.assigned" in actions
    assert "work_item.dispatched" in actions
    print("UNIFIED AGENT WORKITEM REAL-STACK ASSIGN + DISPATCH + RUNTIME BINDING + RUN CORRELATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"UNIFIED AGENT WORKITEM REAL-STACK CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

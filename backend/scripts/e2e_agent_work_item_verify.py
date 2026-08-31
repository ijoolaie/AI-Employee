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

from app.core.database import AsyncSessionLocal
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus

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


async def seed_agent_work_item(tenant_id: uuid.UUID, user_id: uuid.UUID, suffix: str) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    async with AsyncSessionLocal() as db:
        employee = Employee(tenant_id=tenant_id, slug=f"cert-agent-{suffix}", name="Certification Agent", kind="custom", is_active=True)
        db.add(employee)
        await db.flush()
        version = EmployeeVersion(employee_id=employee.id, version_number=1, is_current=True, input_schema={}, output_schema={}, prompt_template="Deterministic certification agent", allowed_tools=[], rules={})
        db.add(version)
        definition = AgentDefinition(tenant_id=tenant_id, slug=f"cert-agent-def-{suffix}", name="Certification Agent Definition", description="Real-stack certification", version=1, capabilities=["certification"], allowed_tools=[], model_policy={}, input_schema={}, output_schema={}, policy_requirements={}, enabled=True)
        db.add(definition)
        await db.flush()
        binding = AgentRuntimeBinding(tenant_id=tenant_id, agent_definition_id=definition.id, employee_version_id=version.id, is_active=True)
        instance = AgentInstance(tenant_id=tenant_id, agent_definition_id=definition.id, name="Certification Agent Instance", configuration={}, status=AgentInstanceStatus.ENABLED, max_concurrency=1, budget_policy={}, enabled=True)
        db.add_all([binding, instance])
        await db.flush()
        item = WorkItem(tenant_id=tenant_id, requester_id=user_id, title="Agent Unified WorkItem runtime acceptance", status=WorkItemStatus.READY, executor_type=ExecutorType.AGENT, input_data={"task": "deterministic agent execution acceptance"}, policy_context={}, idempotency_key=f"agent-unified-work-item-{suffix}")
        db.add(item)
        await db.commit()
        return item.id, instance.id, version.id


async def read_state(work_item_id: uuid.UUID) -> tuple[WorkItemStatus, dict | None, Run | None]:
    async with AsyncSessionLocal() as db:
        item = await db.get(WorkItem, work_item_id)
        assert item is not None
        run_id = (item.output_data or {}).get("run_id")
        run = await db.get(Run, uuid.UUID(run_id)) if run_id else None
        return item.status, item.output_data, run


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    status, registered = request("POST", "/auth/register", {"tenant_name": f"Agent WorkItem Acceptance {suffix}", "tenant_slug": f"cert-agent-work-item-{suffix}", "email": f"i.joolaie+agent-{suffix}@gmail.com", "password": "CertAgentWorkItem-2026!", "full_name": "Agent WorkItem Acceptance User"})
    assert status == 201, registered
    token = (registered.get("data") or {}).get("access_token")
    assert token
    status, me = request("GET", "/auth/me", token=token)
    assert status == 200, me
    data = me.get("data") or {}
    tenant_id = uuid.UUID(str((data.get("tenant") or {}).get("id")))
    user_id = uuid.UUID(str(data.get("user_id")))

    work_item_id, agent_instance_id, version_id = asyncio.run(seed_agent_work_item(tenant_id, user_id, suffix))
    status, assigned = request("POST", f"/work-items/{work_item_id}/assign/agent", {"agent_instance_id": str(agent_instance_id)}, token)
    assert status == 200, assigned
    assert assigned["status"] == "assigned"

    status, dispatched = request("POST", f"/work-items/{work_item_id}/dispatch", token=token)
    assert status == 200, dispatched
    assert dispatched["dispatched"] is True
    assert dispatched["status"] == "running"

    db_status, output, run = asyncio.run(read_state(work_item_id))
    assert db_status is WorkItemStatus.RUNNING, db_status
    assert output and output["executor_type"] == "agent"
    assert output["agent_instance_id"] == str(agent_instance_id)
    assert output["employee_version_id"] == str(version_id)
    assert run is not None
    assert run.tenant_id == tenant_id
    assert run.employee_version_id == version_id
    assert run.employee_id is not None

    status, history = request("GET", f"/work-items/{work_item_id}/history", token=token)
    assert status == 200, history
    actions = {entry["action"] for entry in history}
    assert "work_item.assigned" in actions
    assert "work_item.dispatched" in actions

    print("AGENT WORKITEM REAL-STACK RUNTIME BINDING + RUN CORRELATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"AGENT WORKITEM REAL-STACK CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

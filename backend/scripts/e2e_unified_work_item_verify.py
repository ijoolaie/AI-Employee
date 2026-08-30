"""Real-stack certification for the canonical WorkItem execution API path."""
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
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run

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


async def create_human_work_item(tenant_id: uuid.UUID, suffix: str) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        item = WorkItem(
            tenant_id=tenant_id,
            title="Unified WorkItem human runtime acceptance",
            status=WorkItemStatus.READY,
            executor_type=ExecutorType.HUMAN,
            input_data={"task": "deterministic unified execution acceptance"},
            policy_context={},
            idempotency_key=f"unified-work-item-human-{suffix}",
        )
        db.add(item)
        await db.commit()
        return item.id


async def create_agent_stack(tenant_id: uuid.UUID, suffix: str) -> tuple[uuid.UUID, uuid.UUID]:
    async with AsyncSessionLocal() as db:
        employee = Employee(
            tenant_id=tenant_id,
            slug=f"cert-agent-employee-{suffix}",
            name="Certification Agent Employee",
            kind="custom",
        )
        db.add(employee)
        await db.flush()
        version = EmployeeVersion(
            employee_id=employee.id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="Certification agent runtime",
            allowed_tools=[],
            rules={},
        )
        db.add(version)
        definition = AgentDefinition(
            tenant_id=tenant_id,
            slug=f"cert-agent-definition-{suffix}",
            name="Certification Agent Definition",
            description="Real-stack unified execution certification",
        )
        db.add(definition)
        await db.flush()
        instance = AgentInstance(
            tenant_id=tenant_id,
            agent_definition_id=definition.id,
            name="Certification Agent Instance",
        )
        db.add(instance)
        binding = AgentRuntimeBinding(
            tenant_id=tenant_id,
            agent_definition_id=definition.id,
            employee_version_id=version.id,
            is_active=True,
        )
        db.add(binding)
        await db.flush()
        item = WorkItem(
            tenant_id=tenant_id,
            title="Unified WorkItem agent runtime acceptance",
            status=WorkItemStatus.READY,
            executor_type=ExecutorType.AGENT,
            input_data={"task": "deterministic agent unified execution acceptance"},
            policy_context={},
            idempotency_key=f"unified-work-item-agent-{suffix}",
        )
        db.add(item)
        await db.commit()
        return item.id, instance.id


async def read_work_item(work_item_id: uuid.UUID) -> tuple[WorkItemStatus, dict | None]:
    async with AsyncSessionLocal() as db:
        item = await db.get(WorkItem, work_item_id)
        if item is None:
            raise AssertionError(f"work item disappeared: {work_item_id}")
        return item.status, item.output_data


async def read_run(run_id: uuid.UUID, tenant_id: uuid.UUID) -> Run:
    async with AsyncSessionLocal() as db:
        run = await db.get(Run, run_id)
        if run is None:
            raise AssertionError(f"agent run disappeared: {run_id}")
        assert run.tenant_id == tenant_id
        return run


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    status, registered = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"Unified WorkItem Acceptance {suffix}",
            "tenant_slug": f"cert-unified-work-item-{suffix}",
            "email": f"i.joolaie+unified-{suffix}@gmail.com",
            "password": "CertUnifiedWorkItem-2026!",
            "full_name": "Unified WorkItem Acceptance User",
        },
    )
    assert status == 201, registered
    assert isinstance(registered, dict)
    token = (registered.get("data") or {}).get("access_token")
    assert token

    status, me = request("GET", "/auth/me", token=token)
    assert status == 200, me
    assert isinstance(me, dict)
    tenant_id = uuid.UUID(str(((me.get("data") or {}).get("tenant") or {}).get("id")))

    work_item_id = asyncio.run(create_human_work_item(tenant_id, suffix))
    human_id = uuid.uuid4()

    status, assigned = request(
        "POST",
        f"/work-items/{work_item_id}/assign/human",
        {"executor_id": str(human_id)},
        token,
    )
    assert status == 200, assigned
    assert isinstance(assigned, dict)
    assert assigned["status"] == "assigned"

    status, dispatched = request("POST", f"/work-items/{work_item_id}/dispatch", token=token)
    assert status == 200, dispatched
    assert isinstance(dispatched, dict)
    assert dispatched["status"] == "running"
    assert dispatched["dispatched"] is True
    assert dispatched["waiting_for_approval"] is False

    db_status, output = asyncio.run(read_work_item(work_item_id))
    assert db_status is WorkItemStatus.RUNNING, db_status
    assert output and output["executor_type"] == "human"
    assert output["executor_id"] == str(human_id)

    status, history = request("GET", f"/work-items/{work_item_id}/history", token=token)
    assert status == 200, history
    assert isinstance(history, list)
    actions = {entry["action"] for entry in history}
    assert "work_item.assigned" in actions
    assert "work_item.dispatched" in actions

    agent_work_item_id, agent_instance_id = asyncio.run(create_agent_stack(tenant_id, suffix))
    status, agent_assigned = request(
        "POST",
        f"/work-items/{agent_work_item_id}/assign/agent",
        {"executor_id": str(agent_instance_id)},
        token,
    )
    assert status == 200, agent_assigned
    assert isinstance(agent_assigned, dict)
    assert agent_assigned["status"] == "assigned"

    status, agent_dispatched = request("POST", f"/work-items/{agent_work_item_id}/dispatch", token=token)
    assert status == 200, agent_dispatched
    assert isinstance(agent_dispatched, dict)
    assert agent_dispatched["status"] == "running"
    assert agent_dispatched["dispatched"] is True

    agent_db_status, agent_output = asyncio.run(read_work_item(agent_work_item_id))
    assert agent_db_status is WorkItemStatus.RUNNING, agent_db_status
    assert agent_output and agent_output["executor_type"] == "agent"
    assert agent_output["agent_instance_id"] == str(agent_instance_id)
    run_id = uuid.UUID(str(agent_output["run_id"]))
    run = asyncio.run(read_run(run_id, tenant_id))
    assert str(run.employee_id) == agent_output["employee_id"]
    assert str(run.employee_version_id) == agent_output["employee_version_id"]

    status, agent_history = request("GET", f"/work-items/{agent_work_item_id}/history", token=token)
    assert status == 200, agent_history
    assert isinstance(agent_history, list)
    agent_actions = {entry["action"] for entry in agent_history}
    assert "work_item.assigned" in agent_actions
    assert "work_item.dispatched" in agent_actions

    print("UNIFIED WORKITEM REAL-STACK HUMAN + AGENT ASSIGN + DISPATCH + AUDIT PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"UNIFIED WORKITEM REAL-STACK CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

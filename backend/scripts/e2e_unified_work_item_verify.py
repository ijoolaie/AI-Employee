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


async def create_work_item(tenant_id: uuid.UUID, suffix: str) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        item = WorkItem(
            tenant_id=tenant_id,
            title="Unified WorkItem runtime acceptance",
            status=WorkItemStatus.READY,
            executor_type=ExecutorType.HUMAN,
            input_data={"task": "deterministic unified execution acceptance"},
            policy_context={},
            idempotency_key=f"unified-work-item-{suffix}",
        )
        db.add(item)
        await db.commit()
        return item.id


async def read_work_item(work_item_id: uuid.UUID) -> tuple[WorkItemStatus, dict | None]:
    async with AsyncSessionLocal() as db:
        item = await db.get(WorkItem, work_item_id)
        if item is None:
            raise AssertionError(f"work item disappeared: {work_item_id}")
        return item.status, item.output_data


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
    me_data = me.get("data") or {}
    tenant_id = uuid.UUID(str((me_data.get("tenant") or {}).get("id")))
    human_id = uuid.UUID(str((me_data.get("user") or {}).get("id")))

    # The registered certification user is a real active User in the same
    # tenant.  Assigning that identity exercises the production API contract;
    # an arbitrary UUID would correctly be rejected as a nonexistent executor.
    assert human_id, f"auth/me did not return the certification user id: {me}"

    work_item_id = asyncio.run(create_work_item(tenant_id, suffix))

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

    print("UNIFIED WORKITEM REAL-STACK ASSIGN + DISPATCH + AUDIT PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"UNIFIED WORKITEM REAL-STACK CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

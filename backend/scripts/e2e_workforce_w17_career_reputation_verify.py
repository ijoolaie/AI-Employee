"""Real-stack W17 Employee Career & Reputation evidence E2E.

Mainline trigger reconciliation: execute this harness on push/PR for W17 evidence.

Verifies tenant-scoped read-only career projection from authoritative PostgreSQL
Employee/Run/WorkItem records. No reputation score or fabricated tenure is used.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.user import User
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus


BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def register_tenant(suffix: str):
    payload = json.dumps(
        {
            "tenant_name": f"W17 Career E2E {suffix}",
            "tenant_slug": f"w17-career-{suffix}",
            "email": f"w17-owner-{suffix}@example.com",
            "password": "W17CareerE2E-2026!",
            "full_name": "W17 CEO",
        }
    ).encode()
    with urlopen(
        Request(
            f"{BASE_URL}/auth/register",
            data=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        ),
        timeout=20,
    ) as response:
        data = json.loads(response.read().decode())
        assert response.status == 201, data
        token = data["data"]["access_token"]
    with urlopen(
        Request(
            f"{BASE_URL}/auth/me",
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            method="GET",
        ),
        timeout=20,
    ) as response:
        me = json.loads(response.read().decode())
        assert response.status == 200, me
    return uuid.UUID(me["data"]["tenant"]["id"]), uuid.UUID(me["data"]["user"]["id"]), token


async def seed_authoritative_records(tenant_id, owner_id, suffix):
    async with AsyncSessionLocal() as db:
        employee = Employee(
            tenant_id=tenant_id,
            slug=f"w17-career-employee-{suffix}",
            name="W17 Career Employee",
            kind="custom",
            is_active=True,
        )
        db.add(employee)
        await db.flush()

        version = EmployeeVersion(
            employee_id=employee.id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="W17 deterministic evidence fixture",
            allowed_tools=[],
            rules={},
        )
        db.add(version)
        await db.flush()

        success_item = WorkItem(
            tenant_id=tenant_id,
            title="W17 completed governed work",
            description="Authoritative successful work fixture.",
            status=WorkItemStatus.SUCCEEDED,
            requester_id=owner_id,
            executor_type=ExecutorType.HUMAN,
            executor_id=owner_id,
            input_data={},
            output_data={"fixture": True},
            policy_context={},
            idempotency_key=f"w17-success-{suffix}",
        )
        failed_item = WorkItem(
            tenant_id=tenant_id,
            title="W17 failed work",
            description="Must not count as completed.",
            status=WorkItemStatus.FAILED,
            requester_id=owner_id,
            executor_type=ExecutorType.HUMAN,
            executor_id=owner_id,
            input_data={},
            output_data={},
            policy_context={},
            idempotency_key=f"w17-failed-{suffix}",
        )
        db.add_all([success_item, failed_item])
        await db.flush()

        now = datetime.now(timezone.utc)
        successful_run = Run(
            tenant_id=tenant_id,
            employee_id=employee.id,
            employee_version_id=version.id,
            created_by=owner_id,
            work_item_id=success_item.id,
            status="success",
            input_data={"fixture": True},
            output_data={"result": "ok"},
            started_at=now,
            completed_at=now,
        )
        failed_run = Run(
            tenant_id=tenant_id,
            employee_id=employee.id,
            employee_version_id=version.id,
            created_by=owner_id,
            work_item_id=failed_item.id,
            status="failed",
            input_data={"fixture": True},
            error={"message": "fixture failure"},
            started_at=now,
            completed_at=now,
        )
        db.add_all([successful_run, failed_run])
        await db.commit()
        return employee.id, successful_run.id, success_item.id


def get_career(token, employee_id):
    with urlopen(
        Request(
            f"{BASE_URL}/customer-dashboard/employees/{employee_id}/career",
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            method="GET",
        ),
        timeout=20,
    ) as response:
        assert response.status == 200
        return json.loads(response.read().decode())


def get_cross_tenant(token, employee_id):
    try:
        with urlopen(
            Request(
                f"{BASE_URL}/customer-dashboard/employees/{employee_id}/career",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
                method="GET",
            ),
            timeout=20,
        ) as response:
            raise AssertionError(f"cross-tenant request unexpectedly returned {response.status}")
    except Exception as exc:
        if getattr(exc, "code", None) != 404:
            raise


async def run():
    suffix = str(time.time_ns())[-10:]
    tenant_id, owner_id, token = register_tenant(suffix)
    employee_id, run_id, work_item_id = await seed_authoritative_records(tenant_id, owner_id, suffix)

    payload = get_career(token, employee_id)
    data = payload["data"]

    assert data["contract_version"] == "w17-career-v1"
    assert data["employee"]["id"] == str(employee_id)
    assert data["tenure"]["status"] == "UNKNOWN"
    assert data["indicators"][0]["code"] == "successful_runs"
    assert data["indicators"][0]["value"] == 1
    assert data["indicators"][1]["code"] == "completed_work_items"
    assert data["indicators"][1]["value"] == 1
    assert data["indicators"][2]["evidence_status"] == "NOT_APPLICABLE"
    assert len(data["work_history"]) == 1
    assert data["work_history"][0]["id"] == str(work_item_id)
    assert data["work_history"][0]["run_id"] == str(run_id)
    assert data["achievements"] == []

    other_tenant_id, other_owner_id, other_token = register_tenant(suffix + "-other")
    assert other_tenant_id != tenant_id
    get_cross_tenant(other_token, employee_id)

    print("W17 CAREER API REAL-STACK PASS")
    print("W17 TENANT ISOLATION PASS")
    print("W17 AUTHORITATIVE SUCCESS COUNT PASS")
    print("W17 FAILED WORK EXCLUSION PASS")
    print("W17 UNKNOWN TENURE PASS")
    print("W17 REPUTATION SCORE DEFERRED PASS")
    print("WORKFORCE W17 CAREER-REPUTATION REAL-STACK E2E PASS")


def main():
    try:
        asyncio.run(run())
    except Exception as exc:
        print(f"WORKFORCE W17 CAREER-REPUTATION REAL-STACK E2E FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

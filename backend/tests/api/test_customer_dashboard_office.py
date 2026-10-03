from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import customer_dashboard
from app.services import customer_dashboard_service


class _Result:
    def __init__(self, *, rows=None, scalar_rows=None):
        self._rows = list(rows or [])
        self._scalar_rows = list(scalar_rows or [])

    def all(self):
        return list(self._rows)

    def scalars(self):
        return SimpleNamespace(all=lambda: list(self._scalar_rows))


class _DB:
    def __init__(self, results):
        self.results = iter(results)
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return next(self.results)


@pytest.mark.asyncio
async def test_office_service_is_tenant_scoped_and_preserves_authoritative_state(monkeypatch):
    tenant_id = uuid4()
    employee_id = uuid4()
    run_id = uuid4()
    work_item_id = uuid4()
    approval_id = uuid4()
    step_run_id = uuid4()

    employee = SimpleNamespace(
        id=employee_id,
        tenant_id=tenant_id,
        name="Engineering Employee",
        slug="engineering-employee",
        avatar_url="https://example.test/avatar.png",
        kind="custom",
        is_active=True,
        created_at=None,
    )
    work_item_status = SimpleNamespace(value="running")
    work_item = (work_item_id, "Implement governed change", work_item_status)
    now = datetime.now(timezone.utc)
    approval = SimpleNamespace(
        id=approval_id,
        workflow_run_id=uuid4(),
        workflow_step_run_id=step_run_id,
        step_key="deploy",
        status="pending",
        created_at=now,
        expires_at=None,
    )

    plan = SimpleNamespace(
        code="business", name="Business", features={"analytics": True, "priority": "standard"},
        max_employees=20, max_workflows=25, monthly_runs=2000, monthly_tokens=2_000_000,
    )
    subscription = SimpleNamespace(plan=plan, status="active")
    async def fake_subscription(db, *, tenant_id):
        return subscription
    async def fake_usage(db, *, tenant_id, now=None):
        return {"calls": 3, "tokens": 1200, "runs": 7, "employees": 1, "workflows": 2}
    monkeypatch.setattr(customer_dashboard_service.billing_service, "get_subscription", fake_subscription)
    monkeypatch.setattr(customer_dashboard_service.billing_service, "monthly_usage", fake_usage)

    db = _DB(
        [
            _Result(scalar_rows=[run_id]),
            _Result(rows=[(approval, employee_id, employee.name)]),
            _Result(
                rows=[
                    (
                        employee,
                        run_id,
                        "running",
                        None,
                        work_item[0],
                        work_item[1],
                        work_item[2],
                    )
                ]
            ),
        ]
    )

    office = await customer_dashboard_service.get_office(db, tenant_id=tenant_id)

    assert office["employee_count"] == 1
    assert office["hq_tier"] == "BUSINESS"
    assert office["hq_metrics"]["active_employees"] == 1
    assert office["hq_metrics"]["monthly_runs"] == 7
    assert office["hq_metrics"]["enabled_capabilities"] == ["analytics", "priority"]
    assert office["working_count"] == 0
    assert office["waiting_count"] == 1
    assert office["idle_count"] == 0
    assert office["blocked_count"] == 0
    assert office["escalated_count"] == 0
    assert office["employees"][0]["id"] == str(employee_id)
    assert office["employees"][0]["presentation_state"] == "WAITING_APPROVAL"
    assert office["employees"][0]["latest_run_id"] == str(run_id)
    assert office["employees"][0]["current_work_item"] == {
        "id": str(work_item_id),
        "title": "Implement governed change",
        "status": "running",
    }
    assert office["pending_approvals"][0]["employee_id"] == str(employee_id)
    assert office["pending_approvals"][0]["step_key"] == "deploy"

    sql = [str(statement) for statement in db.statements]
    assert "employees.tenant_id" in sql[2]
    assert "workflow_approvals.tenant_id" in sql[1]
    assert "runs.tenant_id" in sql[0]
    assert "runs.tenant_id" in sql[1]
    assert "work_items.tenant_id" in sql[2]


@pytest.mark.asyncio
async def test_customer_office_route_passes_authenticated_tenant_to_service(monkeypatch):
    tenant_id = uuid4()
    captured = {}
    now = datetime.now(timezone.utc)

    async def fake_get_office(db, *, tenant_id):
        captured["db"] = db
        captured["tenant_id"] = tenant_id
        return {
            "office_state": "LIVE",
            "employee_count": 0,
            "working_count": 0,
            "waiting_count": 0,
            "idle_count": 0,
            "blocked_count": 0,
            "escalated_count": 0,
            "employees": [],
            "pending_approvals": [],
            "generated_at": now,
        }

    monkeypatch.setattr(customer_dashboard.customer_dashboard_service, "get_office", fake_get_office)

    db = object()
    ctx = SimpleNamespace(tenant_id=tenant_id)

    response = await customer_dashboard.get_customer_office(ctx=ctx, db=db)

    assert captured == {"db": db, "tenant_id": tenant_id}
    assert response.success is True
    assert response.data["employee_count"] == 0
    assert response.data["office_state"] == "LIVE"


@pytest.mark.parametrize(
    ("plan_code", "features", "expected"),
    [
        ("starter", {}, "STARTER"),
        ("business", {"analytics": True}, "BUSINESS"),
        ("professional", {"advanced_workflows": True}, "PROFESSIONAL"),
        ("enterprise", {}, "ENTERPRISE"),
        ("custom", {}, "CUSTOM"),
    ],
)
def test_office_hq_tier_is_entitlement_bound(plan_code, features, expected):
    assert customer_dashboard_service._office_hq_tier(plan_code=plan_code, features=features) == expected

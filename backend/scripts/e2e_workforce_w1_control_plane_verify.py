"""Real-stack W1 Internal Manager control-plane E2E certification.

Covers: CEO delegation -> Manager assign_task -> specialist execution -> result
verification -> Manager CEO report. This is evidence only; it does not alter
the immutable v1.4.11 certification.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback

# Allow direct execution from /app/scripts as well as module execution.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.agent_access_review import AgentAccessReviewDecision
from app.models.agent_definition import AgentDefinition
from app.models.agent_evaluation import AgentEvaluationStatus
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.audit_log import AuditLog
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.user import User
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services import edition_service, license_service, agent_tool_governance
from app.services.agent_execution_adapter import AgentExecutionAdapter
from app.services.agent_governance import governed_agent_execution, record_evaluation, review_access
from app.services.agent_template_service import create_template, publish_template
from app.services.agent_workforce_proposal_service import (
    activate_provisioned_proposal,
    board_decide,
    ceo_decide,
    create_proposal,
    provision_approved_proposal,
)
from app.services.ai_workforce_roles import (
    workforce_capability_contract_snapshot,
    workforce_template_capability_contract,
)
from app.services.workforce_delegation_service import create_delegation

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def req(method, path, payload=None, token=None):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method), timeout=20) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        raise AssertionError(f"{method} {path} HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


async def new_user(db, tenant_id, suffix, label):
    user = User(
        tenant_id=tenant_id,
        email=f"w1-{label}-{suffix}@example.com",
        password_hash="fixture",
        full_name=f"W1 {label}",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def license_fixture(tenant_id, suffix):
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
        tenant.tenant_kind = edition_service.EDITION_CUSTOMER
        vendor = Tenant(
            name=f"W1 Vendor {suffix}",
            slug=f"w1-vendor-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_VENDOR,
        )
        db.add(vendor)
        await db.flush()
        reseller = Tenant(
            name=f"W1 Reseller {suffix}",
            slug=f"w1-reseller-{suffix}",
            status="active",
            tenant_kind=edition_service.EDITION_RESELLER,
            parent_tenant_id=vendor.id,
        )
        db.add(reseller)
        await db.flush()
        tenant.parent_tenant_id = reseller.id
        row = await license_service.issue_license(
            db,
            issuer=reseller,
            tenant=tenant,
            feature_codes=[
                "employee.run",
                "tool:workforce_assign_task",
                "tool:workforce_prepare_ceo_report",
                "tool:workforce_market_research",
            ],
            metadata={"certification_fixture": True, "purpose": "workforce-w1-control-plane-e2e"},
        )
        assert row.status == "active"
        await db.commit()


async def provision_agent(tenant_id, suffix, owner_id, role_code, label, allowed_tools):
    async with AsyncSessionLocal() as db:
        sponsor = await new_user(db, tenant_id, suffix, f"sponsor-{label}")
        board = await new_user(db, tenant_id, suffix, f"board-{label}")
        ceo = await new_user(db, tenant_id, suffix, f"ceo-{label}")
        activator = await new_user(db, tenant_id, suffix, f"activator-{label}")

        employee = Employee(
            tenant_id=tenant_id,
            slug=f"w1-{label}-{suffix}",
            name=f"W1 {label}",
            kind="custom",
            is_active=True,
        )
        db.add(employee)
        await db.flush()

        output = {"type": "object", "properties": {"content": {"type": "string"}}}
        version = EmployeeVersion(
            employee_id=employee.id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema=output,
            prompt_template=f"Operate as governed {label}.",
            allowed_tools=list(allowed_tools),
            rules={},
        )
        definition = AgentDefinition(
            tenant_id=tenant_id,
            slug=f"w1-{label}-def-{suffix}",
            name=f"W1 {label}",
            capabilities=["execution"],
            allowed_tools=list(allowed_tools),
            model_policy={},
            input_schema={},
            output_schema=output,
            policy_requirements={},
            enabled=True,
        )
        db.add_all([version, definition])
        await db.flush()

        template = await create_template(
            db,
            tenant_id=tenant_id,
            agent_definition_id=definition.id,
            slug=f"w1-{label}-template-{suffix}",
            name=f"W1 {label} Template",
            version=1,
            risk_tier=0,
            capability_contract=workforce_template_capability_contract(role_code),
            permission_policy={"permissions": ["run.execute"], "allowed_tools": list(allowed_tools)},
            approval_policy={},
            evaluation_policy={},
            install_policy={"requires_ceo_approval": True},
        )
        await record_evaluation(
            db,
            tenant_id=tenant_id,
            template_id=template.id,
            suite_id="workforce-w1-control-plane-v1",
            status=AgentEvaluationStatus.PASSED,
            evidence={"contract_version": "v1", "fixture": True, "role": role_code},
            score=100,
            evaluator_user_id=board.id,
            notes="W1 E2E fixture",
        )
        await publish_template(db, tenant_id=tenant_id, template_id=template.id, approved_by_user_id=ceo.id)

        configuration = {
            "workforce_role_code": role_code,
            "workforce_capability_contract": workforce_capability_contract_snapshot(role_code),
            "max_concurrency": 1,
            "budget_policy": {},
            "e2e_variant": label,
        }
        proposal = await create_proposal(
            db,
            tenant_id=tenant_id,
            requester_user_id=owner_id,
            title=f"W1 {label}",
            rationale="W1 Internal Manager control-plane certification",
            requested_name=f"W1 {label}",
            sponsor_user_id=sponsor.id,
            agent_template_id=template.id,
            risk_tier=0,
            configuration=configuration,
        )
        await board_decide(db, tenant_id=tenant_id, proposal_id=proposal.id, reviewer_user_id=board.id, approve=True, reason="W1 E2E")
        await ceo_decide(db, tenant_id=tenant_id, proposal_id=proposal.id, approver_user_id=ceo.id, approve=True, reason="W1 E2E")
        await provision_approved_proposal(db, tenant_id=tenant_id, proposal_id=proposal.id)
        instance_id = proposal.provisioned_agent_instance_id
        identity = (
            await db.execute(
                select(AgentIdentity).where(
                    AgentIdentity.agent_instance_id == instance_id,
                    AgentIdentity.tenant_id == tenant_id,
                )
            )
        ).scalar_one()
        await review_access(
            db,
            tenant_id=tenant_id,
            identity_id=identity.id,
            reviewer_user_id=activator.id,
            decision=AgentAccessReviewDecision.APPROVED,
            next_review_at=None,
            reason="W1 E2E",
        )
        await activate_provisioned_proposal(
            db,
            tenant_id=tenant_id,
            proposal_id=proposal.id,
            activated_by_user_id=activator.id,
        )
        db.add(
            AgentRuntimeBinding(
                tenant_id=tenant_id,
                agent_definition_id=definition.id,
                employee_version_id=version.id,
                is_active=True,
            )
        )
        await db.commit()
        return instance_id, version.employee_id, version.id


async def create_work_item(tenant_id, owner_id, suffix, agent_id):
    async with AsyncSessionLocal() as db:
        item = WorkItem(
            tenant_id=tenant_id,
            title=f"W1 specialist task {suffix}",
            description="Deterministic specialist task delegated by the Internal Manager.",
            status=WorkItemStatus.READY,
            requester_id=owner_id,
            executor_type=ExecutorType.AGENT,
            executor_id=agent_id,
            input_data={"request": "market research", "symbols": ["AAPL"]},
            policy_context={},
            idempotency_key=f"w1-specialist-{suffix}",
        )
        db.add(item)
        await db.commit()
        return item.id


async def create_manager_run(tenant_id, manager_id, employee_id, employee_version_id, owner_id):
    async with AsyncSessionLocal() as db:
        run = Run(
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=employee_version_id,
            agent_instance_id=manager_id,
            created_by=owner_id,
            status="pending",
            input_data={"objective": "coordinate specialist and report to CEO"},
        )
        db.add(run)
        await db.commit()
        return run.id


async def wait_result(work_item_id):
    for _ in range(100):
        async with AsyncSessionLocal() as db:
            item = await db.get(WorkItem, work_item_id)
            if item and item.status in {WorkItemStatus.SUCCEEDED, WorkItemStatus.FAILED}:
                run_id = (item.output_data or {}).get("run_id")
                run = await db.get(Run, uuid.UUID(run_id)) if run_id else None
                return item, run
        await asyncio.sleep(0.25)
    raise AssertionError("W1 specialist WorkItem execution timed out")


async def verify_specialist_result(tenant_id, work_item_id):
    async with AsyncSessionLocal() as db:
        item = await db.get(WorkItem, work_item_id)
        assert item and item.status is WorkItemStatus.SUCCEEDED, item.status if item else None
        run_id = (item.output_data or {}).get("run_id")
        assert run_id
        run = await db.get(Run, uuid.UUID(run_id))
        assert run and run.status == "success"
        audit = (
            await db.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.resource_type == "run",
                    AuditLog.resource_id == str(run.id),
                    AuditLog.action == "tool.call",
                )
            )
        ).scalars().all()
        assert audit
        return run


async def run():
    suffix = str(time.time_ns())[-10:]
    status, data = req(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"W1 Internal Manager E2E {suffix}",
            "tenant_slug": f"w1-internal-manager-{suffix}",
            "email": f"w1-owner-{suffix}@example.com",
            "password": "W1InternalManagerE2E-2026!",
            "full_name": "W1 CEO",
        },
    )
    assert status == 201, data
    token = data["data"]["access_token"]
    status, me = req("GET", "/auth/me", token=token)
    assert status == 200, me
    tenant_id = uuid.UUID(str(me["data"]["tenant"]["id"]))
    owner_id = uuid.UUID(str(me["data"]["user"]["id"]))

    await license_fixture(tenant_id, suffix)
    manager_id, manager_employee_id, manager_version_id = await provision_agent(
        tenant_id,
        suffix,
        owner_id,
        "ai_internal_manager",
        "internal-manager",
        ["workforce_assign_task", "workforce_prepare_ceo_report"],
    )
    specialist_id, _, _ = await provision_agent(
        tenant_id,
        suffix,
        owner_id,
        "ai_trader",
        "specialist-trader",
        ["workforce_market_research"],
    )
    work_item_id = await create_work_item(tenant_id, owner_id, suffix, specialist_id)

    async with AsyncSessionLocal() as db:
        delegation = await create_delegation(
            db,
            tenant_id=tenant_id,
            manager_agent_instance_id=manager_id,
            delegated_by_user_id=owner_id,
            starts_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            allowed_operations=["assign_task", "prepare_ceo_report"],
            scope={"purpose": "W1 control-plane E2E"},
            resource_limits={"max_assignments": 1},
            risk_tier=0,
        )
        await db.commit()
        delegation_id = delegation.id

    async with AsyncSessionLocal() as db:
        manager = (
            await db.execute(
                select(AgentInstance).where(
                    AgentInstance.id == manager_id,
                    AgentInstance.tenant_id == tenant_id,
                )
            )
        ).scalar_one()
        manager_run_id = await create_manager_run(
            tenant_id, manager_id, manager_employee_id, manager_version_id, owner_id
        )

        async with governed_agent_execution(
            tenant_id=tenant_id,
            agent_instance_id=manager_id,
            run_id=manager_run_id,
            employee_id=manager_employee_id,
            employee_version_id=manager_version_id,
            delegation_id=delegation_id,
        ):
            async with agent_tool_governance.agent_tool_context(
                tenant_id=tenant_id,
                agent_instance_id=manager_id,
                run_id=manager_run_id,
                delegation_id=delegation_id,
            ):
                adapter = AgentExecutionAdapter(db)
                assigned = await adapter.execute_tool(
                agent=manager,
                tool_name="workforce_assign_task",
                workforce_operation="assign_task",
                    arguments={"work_item_id": str(work_item_id), "agent_instance_id": str(specialist_id)},
                )
                assert assigned["status"] == WorkItemStatus.ASSIGNED.value
                await db.commit()

    status, payload = req("POST", f"/work-items/{work_item_id}/dispatch", token=token)
    assert status == 200, payload
    specialist_item, _ = await wait_result(work_item_id)
    specialist_run = await verify_specialist_result(tenant_id, work_item_id)

    async with AsyncSessionLocal() as db:
        manager = (
            await db.execute(
                select(AgentInstance).where(
                    AgentInstance.id == manager_id,
                    AgentInstance.tenant_id == tenant_id,
                )
            )
        ).scalar_one()
        async with governed_agent_execution(
            tenant_id=tenant_id,
            agent_instance_id=manager_id,
            run_id=manager_run_id,
            employee_id=manager_employee_id,
            employee_version_id=manager_version_id,
            delegation_id=delegation_id,
        ):
            async with agent_tool_governance.agent_tool_context(
                tenant_id=tenant_id,
                agent_instance_id=manager_id,
                run_id=manager_run_id,
                delegation_id=delegation_id,
            ):
                report = await AgentExecutionAdapter(db).execute_tool(
                agent=manager,
                tool_name="workforce_prepare_ceo_report",
                workforce_operation="prepare_ceo_report",
                    arguments={"window_days": 1},
                )
                assert report["work_items"]["status_counts"].get("succeeded", 0) >= 1
                await db.commit()

    print("W1 CEO DELEGATION PASS")
    print("W1 MANAGER ASSIGN_TASK PASS")
    print(f"W1 SPECIALIST RESULT PASS run={specialist_run.id}")
    print("W1 CEO REPORT VERIFICATION PASS")
    print("WORKFORCE W1 CONTROL-PLANE REAL-STACK E2E PASS")


def main():
    try:
        asyncio.run(run())
    except AssertionError as exc:
        print(f"WORKFORCE W1 CONTROL-PLANE REAL-STACK E2E FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"WORKFORCE W1 CONTROL-PLANE REAL-STACK E2E ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()

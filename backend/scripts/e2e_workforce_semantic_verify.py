"""Real-stack semantic Workforce E2E matrix.

This is an E2E-only certification script. It provisions an AI Trader through
the governed proposal/template/access-review path, dispatches real Agent
WorkItems, and verifies the real Celery Run -> ToolRegistry -> market-provider
path plus negative role/capability checks.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.agent_definition import AgentDefinition
from app.models.agent_evaluation import AgentEvaluationStatus
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.agent_template import AgentTemplate
from app.models.audit_log import AuditLog
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.user import User
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services import edition_service, license_service
from app.services.agent_governance import record_evaluation, review_access
from app.services.agent_workforce_proposal_service import (
    activate_provisioned_proposal,
    board_decide,
    ceo_decide,
    create_proposal,
    provision_approved_proposal,
)
from app.services.agent_template_service import create_template, publish_template
from app.services.ai_workforce_roles import workforce_capability_contract_snapshot, workforce_template_capability_contract
from app.services.workforce_runtime_governance import assert_workforce_operation

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, object]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else None
    except (HTTPError, URLError) as exc:
        if isinstance(exc, HTTPError):
            raw = exc.read().decode()
            try:
                detail = json.loads(raw)
            except json.JSONDecodeError:
                detail = {"raw": raw}
            raise AssertionError(f"{method} {path} HTTP {exc.code}: {detail}") from exc
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


async def create_user(db, tenant_id, suffix, label):
    user = User(
        tenant_id=tenant_id,
        email=f"e2e-{label}-{suffix}@example.invalid",
        password_hash="e2e-certification-fixture",
        full_name=f"E2E {label}",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def provision_license(tenant_id, suffix):
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(__import__("app.models.tenant", fromlist=["Tenant"]).Tenant).where(
            __import__("app.models.tenant", fromlist=["Tenant"]).Tenant.id == tenant_id
        ))).scalar_one()
        tenant.tenant_kind = edition_service.EDITION_CUSTOMER
        vendor = __import__("app.models.tenant", fromlist=["Tenant"]).Tenant(
            name=f"E2E Vendor {suffix}", slug=f"e2e-vendor-{suffix}",
            status="active", tenant_kind=edition_service.EDITION_VENDOR,
        )
        db.add(vendor)
        await db.flush()
        reseller = __import__("app.models.tenant", fromlist=["Tenant"]).Tenant(
            name=f"E2E Reseller {suffix}", slug=f"e2e-reseller-{suffix}",
            status="active", tenant_kind=edition_service.EDITION_RESELLER,
            parent_tenant_id=vendor.id,
        )
        db.add(reseller)
        await db.flush()
        tenant.parent_tenant_id = reseller.id
        tenant.vendor_release_tag = "v1.4.11"
        tenant.delivery_revision = "workforce-semantic-e2e"
        license_row = await license_service.issue_license(
            db, issuer=reseller, tenant=tenant,
            feature_codes=["employee.run"],
            metadata={"certification_fixture": True, "purpose": "workforce-semantic-e2e"},
        )
        assert license_row.status == "active"
        await db.commit()


async def create_governed_trader(tenant_id, suffix, owner_id, variant):
    async with AsyncSessionLocal() as db:
        sponsor = await create_user(db, tenant_id, suffix, f"sponsor-{variant}")
        board = await create_user(db, tenant_id, suffix, f"board-{variant}")
        ceo = await create_user(db, tenant_id, suffix, f"ceo-{variant}")
        activator = await create_user(db, tenant_id, suffix, f"activator-{variant}")

        employee = Employee(
            tenant_id=tenant_id, slug=f"e2e-trader-employee-{suffix}-{variant}",
            name=f"E2E Trader Employee {variant}", kind="custom", is_active=True,
        )
        db.add(employee)
        await db.flush()
        version = EmployeeVersion(
            employee_id=employee.id, version_number=1, is_current=True,
            input_schema={}, output_schema={
                "type": "object", "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
            prompt_template="Run deterministic market research for the certification fixture.",
            allowed_tools=["workforce_market_research"],
            rules={},
        )
        definition = AgentDefinition(
            tenant_id=tenant_id, slug=f"e2e-trader-definition-{suffix}-{variant}",
            name=f"E2E Trader Definition {variant}", capabilities=["execution"],
            allowed_tools=["workforce_market_research"], model_policy={},
            input_schema={}, output_schema=version.output_schema,
            policy_requirements={}, enabled=True,
        )
        db.add_all([version, definition])
        await db.flush()

        contract = workforce_template_capability_contract("ai_trader")
        template = await create_template(
            db, tenant_id=tenant_id, agent_definition_id=definition.id,
            slug=f"e2e-trader-template-{suffix}-{variant}",
            name=f"E2E Trader Template {variant}", version=1, risk_tier=0,
            capability_contract=contract,
            permission_policy={"permissions": ["run.execute"], "allowed_tools": ["workforce_market_research"]},
            approval_policy={}, evaluation_policy={},
            install_policy={"requires_ceo_approval": True},
        )
        await record_evaluation(
            db, tenant_id=tenant_id, template_id=template.id,
            suite_id="workforce-semantic-e2e-v1",
            status=AgentEvaluationStatus.PASSED,
            evidence={"contract_version": "v1", "fixture": True, "scope": "workforce-semantic-e2e"},
            score=100, evaluator_user_id=board.id,
            notes="Deterministic E2E governance fixture.",
        )
        await publish_template(db, tenant_id=tenant_id, template_id=template.id, approved_by_user_id=ceo.id)

        config = {
            "workforce_role_code": "ai_trader",
            "workforce_capability_contract": workforce_capability_contract_snapshot("ai_trader"),
            "max_concurrency": 1,
            "budget_policy": {},
            "e2e_variant": variant,
        }
        proposal = await create_proposal(
            db, tenant_id=tenant_id, requester_user_id=owner_id,
            title=f"Governed Trader E2E {variant}",
            rationale="Real-stack semantic Workforce certification fixture.",
            requested_name=f"Governed Trader {variant}",
            sponsor_user_id=sponsor.id, agent_template_id=template.id,
            risk_tier=0, configuration=config,
        )
        await board_decide(db, tenant_id=tenant_id, proposal_id=proposal.id,
                           reviewer_user_id=board.id, approve=True, reason="E2E board approval")
        await ceo_decide(db, tenant_id=tenant_id, proposal_id=proposal.id,
                          approver_user_id=ceo.id, approve=True, reason="E2E CEO approval")
        await provision_approved_proposal(db, tenant_id=tenant_id, proposal_id=proposal.id)

        instance_id = proposal.provisioned_agent_instance_id
        identity = (await db.execute(select(AgentIdentity).where(
            AgentIdentity.agent_instance_id == instance_id,
            AgentIdentity.tenant_id == tenant_id,
        ))).scalar_one()
        await review_access(
            db, tenant_id=tenant_id, identity_id=identity.id,
            reviewer_user_id=activator.id,
            decision=__import__("app.models.agent_access_review", fromlist=["AgentAccessReviewDecision"]).AgentAccessReviewDecision.APPROVED,
            next_review_at=None, reason="E2E access review",
        )
        await activate_provisioned_proposal(
            db, tenant_id=tenant_id, proposal_id=proposal.id,
            activated_by_user_id=activator.id,
        )

        instance = (await db.execute(select(AgentInstance).where(
            AgentInstance.id == instance_id, AgentInstance.tenant_id == tenant_id
        ))).scalar_one()
        db.add(AgentRuntimeBinding(
            tenant_id=tenant_id, agent_definition_id=definition.id,
            employee_version_id=version.id, is_active=True,
        ))
        await db.commit()
        return instance.id, version.id


async def create_work_item(tenant_id, agent_id, version_id, suffix, variant):
    async with AsyncSessionLocal() as db:
        item = WorkItem(
            tenant_id=tenant_id, title=f"Semantic Workforce E2E {variant}",
            status=WorkItemStatus.READY, executor_type=ExecutorType.AGENT,
            executor_id=agent_id,
            input_data={"request": "perform deterministic market research"},
            policy_context={}, idempotency_key=f"semantic-workforce-{suffix}-{variant}",
        )
        db.add(item)
        await db.commit()
        return item.id


async def wait_for_run(work_item_id, expected_status="success"):
    last = None
    for _ in range(80):
        async with AsyncSessionLocal() as db:
            item = await db.get(WorkItem, work_item_id)
            if item is not None:
                last = item.status.value
                if item.status.value == "failed":
                    run_id = (item.output_data or {}).get("run_id")
                    run = await db.get(Run, uuid.UUID(run_id)) if run_id else None
                    return False, item, run
                if item.status.value == expected_status and item.output_data:
                    run_id = (item.output_data or {}).get("run_id")
                    run = await db.get(Run, uuid.UUID(run_id)) if run_id else None
                    if run is not None:
                        return True, item, run
        time.sleep(0.25)
    raise AssertionError(f"WorkItem did not reach {expected_status}; last={last}")


async def assert_tool_audit(tenant_id, run_id):
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(AuditLog).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.resource_type == "run",
                AuditLog.resource_id == str(run_id),
                AuditLog.action == "tool.call",
            )
        )).scalars().all()
        assert rows, "missing tool.call audit"
        row = rows[-1]
        metadata = row.metadata_ or {}
        assert metadata.get("tool") == "workforce_market_research"
        assert metadata.get("tool_call_id") == "e2e-workforce-market-research-1"
        assert row.status == "success"


async def assert_denied_operation(tenant_id, agent_id):
    async with AsyncSessionLocal() as db:
        agent = (await db.execute(select(AgentInstance).where(
            AgentInstance.id == agent_id, AgentInstance.tenant_id == tenant_id
        ))).scalar_one()
        try:
            await assert_workforce_operation(db, agent=agent, operation="order_execution")
        except Exception as exc:
            assert "approval" in str(exc).lower()
            return
        raise AssertionError("approval-required order_execution was not denied")


async def main_async(token, tenant_id, owner_id, suffix):
    await provision_license(tenant_id, suffix)

    good_agent, version_id = await create_governed_trader(tenant_id, suffix, owner_id, "allowed")
    good_item = await create_work_item(tenant_id, good_agent, version_id, suffix, "allowed")
    status, payload = request("POST", f"/work-items/{good_item}/assign/agent",
                             {"agent_instance_id": str(good_agent)}, token=token)
    assert status == 200, payload
    status, payload = request("POST", f"/work-items/{good_item}/dispatch", token=token)
    assert status == 200, payload
    ok, item, run = await wait_for_run(good_item)
    assert ok and run is not None and run.status.value == "success"
    assert (run.output_data or {}).get("content")
    await assert_tool_audit(tenant_id, run.id)
    print("WORKFORCE SEMANTIC ALLOWED TOOL REAL-STACK PASS")

    wrong_agent, wrong_version = await create_governed_trader(tenant_id, suffix, owner_id, "wrong-role")
    async with AsyncSessionLocal() as db:
        agent = (await db.execute(select(AgentInstance).where(
            AgentInstance.id == wrong_agent, AgentInstance.tenant_id == tenant_id
        ))).scalar_one()
        agent.configuration = {
            **agent.configuration,
            "workforce_role_code": "ai_marketing_advertising_manager",
        }
        await db.commit()
    wrong_item = await create_work_item(tenant_id, wrong_agent, wrong_version, suffix, "wrong-role")
    status, payload = request("POST", f"/work-items/{wrong_item}/assign/agent",
                             {"agent_instance_id": str(wrong_agent)}, token=token)
    assert status == 200, payload
    status, payload = request("POST", f"/work-items/{wrong_item}/dispatch", token=token)
    assert status == 200, payload
    ok, item, run = await wait_for_run(wrong_item)
    assert not ok and run is not None and run.status.value == "failed"
    assert "not bound to the executing Agent role" in (run.error_message or "")
    print("WORKFORCE SEMANTIC WRONG-ROLE DENIAL REAL-STACK PASS")

    await assert_denied_operation(tenant_id, good_agent)
    print("WORKFORCE SEMANTIC APPROVAL-REQUIRED DENIAL GOVERNANCE PASS")

    return 0


def main() -> int:
    suffix = str(time.time_ns())[-10:]
    status, registered = request(
        "POST", "/auth/register",
        {
            "tenant_name": f"Workforce Semantic E2E {suffix}",
            "tenant_slug": f"workforce-semantic-{suffix}",
            "email": f"workforce-semantic-{suffix}@example.invalid",
            "password": "WorkforceSemanticE2E-2026!",
            "full_name": "Workforce Semantic E2E Owner",
        },
    )
    assert status == 201, registered
    token = (registered.get("data") or {}).get("access_token")
    assert token
    status, me = request("GET", "/auth/me", token=token)
    assert status == 200, me
    tenant_id = uuid.UUID(str(((me.get("data") or {}).get("tenant") or {}).get("id")))
    asyncio.run(main_async(token, tenant_id, uuid.UUID(str(((me.get("data") or {}).get("user") or {}).get("id"))), suffix))
    print("WORKFORCE SEMANTIC REAL-STACK E2E MATRIX PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"WORKFORCE SEMANTIC REAL-STACK E2E MATRIX FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

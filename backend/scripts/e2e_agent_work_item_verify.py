"""Real-stack certification for Agent WorkItem -> runtime binding -> Run correlation."""
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

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.user import User
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services import edition_service, license_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")
MAX_429_RETRIES = 3


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, object]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(MAX_429_RETRIES + 1):
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
            if exc.code == 429 and attempt < MAX_429_RETRIES:
                retry_after = exc.headers.get("Retry-After")
                try:
                    delay = max(1.0, min(10.0, float(retry_after))) if retry_after else 2.0
                except (TypeError, ValueError):
                    delay = 2.0
                time.sleep(delay)
                continue
            raise AssertionError(f"{method} {path} returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise AssertionError(f"{method} {path} unavailable: {exc}") from exc

    raise AssertionError(f"{method} {path} exhausted HTTP 429 retries")


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

        owner = (await db.execute(select(User).where(User.tenant_id == tenant_id, User.is_active.is_(True)).order_by(User.created_at.asc()).limit(1))).scalar_one_or_none()
        if owner is None:
            raise AssertionError(f"Certification owner user not found for tenant: {tenant_id}")
        reviewer = User(
            tenant_id=tenant_id,
            email=f"agent-cert-reviewer-{suffix}@example.invalid",
            password_hash="certification-fixture",
            full_name="Agent Certification Independent Reviewer",
            is_active=True,
        )
        db.add(reviewer)
        await db.flush()

        template = AgentTemplate(
            tenant_id=tenant_id,
            agent_definition_id=definition.id,
            slug=f"cert-agent-template-{suffix}",
            name="Agent Certification Template",
            version=1,
            status=AgentTemplateStatus.PUBLISHED,
            risk_tier=0,
            capability_contract={"execution": True},
            permission_policy={"permissions": ["run.execute"], "allowed_tools": []},
            approval_policy={},
            evaluation_policy={"certification_fixture": True},
            install_policy={},
            published_at=datetime.now(timezone.utc),
        )
        db.add(template)
        await db.flush()

        configuration: dict = {}
        fingerprint = execution_authority_fingerprint(
            tenant_id=tenant_id,
            template_id=template.id,
            template_version=template.version,
            agent_definition_id=definition.id,
            risk_tier=template.risk_tier,
            capability_contract=template.capability_contract,
            permission_policy=template.permission_policy,
            approval_policy=template.approval_policy,
            install_policy=template.install_policy,
            configuration=configuration,
            max_concurrency=1,
            budget_policy={},
        )
        agent_id = uuid.uuid4()
        instance = AgentInstance(
            id=agent_id,
            tenant_id=tenant_id,
            agent_definition_id=definition.id,
            agent_template_id=template.id,
            sponsor_user_id=owner.id,
            name="Agent Certification Instance",
            configuration={**configuration, FINGERPRINT_KEY: fingerprint},
            permission_policy=template.permission_policy,
            approval_policy=template.approval_policy,
            risk_tier=template.risk_tier,
            status=AgentInstanceStatus.ENABLED,
            max_concurrency=1,
            budget_policy={},
            enabled=True,
        )
        db.add(instance)
        await db.flush()
        db.add(
            AgentIdentity(
                tenant_id=tenant_id,
                agent_instance_id=agent_id,
                owner_user_id=owner.id,
                sponsor_user_id=owner.id,
                subject=f"agent:{tenant_id}:{agent_id}",
                active=True,
            )
        )
        await db.flush()
        identity = (await db.execute(select(AgentIdentity).where(AgentIdentity.agent_instance_id == agent_id, AgentIdentity.tenant_id == tenant_id))).scalar_one()
        db.add(
            AgentAccessReview(
                tenant_id=tenant_id,
                agent_identity_id=identity.id,
                reviewer_user_id=reviewer.id,
                decision=AgentAccessReviewDecision.APPROVED,
                reason="Production certification governed-runtime fixture",
            )
        )
        db.add(AgentRuntimeBinding(tenant_id=tenant_id, agent_definition_id=definition.id, employee_version_id=version.id, is_active=True))
        await db.commit()
        return agent_id, version.id


async def create_agent_work_item(tenant_id: uuid.UUID, agent_id: uuid.UUID, suffix: str) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        item = WorkItem(tenant_id=tenant_id, title="Unified Agent WorkItem runtime acceptance", status=WorkItemStatus.READY, executor_type=ExecutorType.AGENT, executor_id=agent_id, input_data={"task": "deterministic agent execution acceptance"}, policy_context={}, idempotency_key=f"agent-unified-work-item-{suffix}")
        db.add(item)
        await db.commit()
        return item.id


async def verify_runtime(work_item_id: uuid.UUID, tenant_id: uuid.UUID, agent_id: uuid.UUID, version_id: uuid.UUID) -> None:
    """Verify the durable WorkItem/Run binding after the dispatch transaction commits."""
    last_state: dict[str, object] = {}
    for _ in range(20):
        async with AsyncSessionLocal() as db:
            item = await db.get(WorkItem, work_item_id)
            if item is not None:
                last_state = {"status": item.status.value, "output_data": item.output_data}
                if item.status is WorkItemStatus.RUNNING and item.output_data and item.output_data.get("executor_type") == "agent":
                    if item.output_data.get("agent_instance_id") != str(agent_id):
                        raise AssertionError(f"agent instance mismatch: {last_state}")
                    if item.output_data.get("employee_version_id") != str(version_id):
                        raise AssertionError(f"employee version mismatch: {last_state}")
                    run_id = uuid.UUID(str(item.output_data["run_id"]))
                    run = await db.get(Run, run_id)
                    if run is None:
                        raise AssertionError(f"run not visible yet: {last_state}")
                    if run.tenant_id != tenant_id:
                        raise AssertionError(f"run tenant mismatch: {run.tenant_id} != {tenant_id}")
                    if run.employee_version_id != version_id:
                        raise AssertionError(f"run employee version mismatch: {run.employee_version_id} != {version_id}")
                    return
                if item.status is WorkItemStatus.FAILED:
                    raise AssertionError(f"agent WorkItem failed: {last_state}")
        time.sleep(0.25)
    raise AssertionError(f"agent runtime binding not visible after dispatch: {last_state}")


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

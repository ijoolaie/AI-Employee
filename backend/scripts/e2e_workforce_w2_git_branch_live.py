"""Controlled live certification of the governed workforce git_branch write path."""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from app.core.database import AsyncSessionLocal
from app.core.config import get_settings
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.agent_instance import AgentInstance
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.models.tool_approval import ToolApprovalRequest
from app.models.user import User
from app.models.tenant import Tenant
from app.models.agent_definition import AgentDefinition
from app.models.agent_identity import AgentIdentity
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.services import agent_tool_governance, edition_service, license_service
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint
from app.ai.tool_registry import registry

REPO = "ijoolaie/AI-Employee"
TOKEN = os.environ["ENGINEERING_GITHUB_TOKEN"]
SOURCE_SHA = os.environ["GITHUB_SHA"]
BRANCH = os.environ.get("W2_LIVE_BRANCH", f"ai-cert/w2-git-branch-{os.environ.get('GITHUB_RUN_ID', uuid.uuid4().hex[:8])}")



def assert_branch_absent() -> None:
    req = Request(
        f"https://api.github.com/repos/{REPO}/git/refs/heads/{BRANCH}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Employee-W2-Live-Certification",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=10):
            raise RuntimeError(f"Refusing certification: branch already exists: {BRANCH}")
    except HTTPError as exc:
        if exc.code == 404:
            return
        raise RuntimeError(f"Unable to prove certification branch is absent: HTTP {exc.code}") from exc

async def prepare() -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, str]:
    suffix = f"{os.environ.get('GITHUB_RUN_ID', 'local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor = Tenant(name=f"Live Cert Vendor {suffix}", slug=f"live-cert-vendor-{suffix}", status="active", tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor); await db.flush()
        reseller = Tenant(name=f"Live Cert Reseller {suffix}", slug=f"live-cert-reseller-{suffix}", status="active", tenant_kind=edition_service.EDITION_RESELLER, parent_tenant_id=vendor.id)
        customer = Tenant(name=f"Live Cert Customer {suffix}", slug=f"live-cert-customer-{suffix}", status="active", tenant_kind=edition_service.EDITION_CUSTOMER, parent_tenant_id=reseller.id)
        db.add_all([reseller, customer]); await db.flush()
        owner = User(tenant_id=customer.id, email=f"live-cert-owner-{suffix}@example.invalid", password_hash="certification-fixture", full_name="Live Certification Requester", is_active=True)
        reviewer = User(tenant_id=customer.id, email=f"live-cert-reviewer-{suffix}@example.invalid", password_hash="certification-fixture", full_name="Live Certification Independent Reviewer", is_active=True)
        db.add_all([owner, reviewer]); await db.flush()
        settings = get_settings()
        settings.engineering_provider_name = "github"
        settings.engineering_github_repositories[str(customer.id)] = REPO
        settings.engineering_github_token = TOKEN
        await license_service.issue_license(db, issuer=reseller, tenant=customer, feature_codes=["employee.run", "tool:workforce_git_branch"], metadata={"certification_fixture": True, "purpose": "W2-live-git-branch"})
        employee = Employee(tenant_id=customer.id, slug=f"live-cert-employee-{suffix}", name="Live Git Branch Certification Employee", kind="custom", is_active=True)
        db.add(employee); await db.flush()
        version = EmployeeVersion(employee_id=employee.id, version_number=1, is_current=True, input_schema={}, output_schema={}, prompt_template="Live Git Branch Certification", allowed_tools=["workforce_git_branch"], rules={})
        definition = AgentDefinition(tenant_id=customer.id, slug=f"live-cert-definition-{suffix}", name="Live Git Branch Certification Definition", capabilities=["execution"], allowed_tools=["workforce_git_branch"], model_policy={}, input_schema={}, output_schema={}, policy_requirements={}, enabled=True)
        db.add_all([version, definition]); await db.flush()
        permission_policy = {"permissions": ["run.execute"], "allowed_tools": ["workforce_git_branch"]}
        template = AgentTemplate(tenant_id=customer.id, agent_definition_id=definition.id, slug=f"live-cert-template-{suffix}", name="Live Git Branch Certification Template", version=1, status=AgentTemplateStatus.PUBLISHED, risk_tier=0, capability_contract={"execution": True}, permission_policy=permission_policy, approval_policy={}, evaluation_policy={"certification_fixture": True}, install_policy={}, published_at=datetime.now(timezone.utc))
        db.add(template); await db.flush()
        fingerprint = execution_authority_fingerprint(tenant_id=customer.id, template_id=template.id, template_version=template.version, agent_definition_id=definition.id, risk_tier=template.risk_tier, capability_contract=template.capability_contract, permission_policy=permission_policy, approval_policy=template.approval_policy, install_policy=template.install_policy, configuration={}, max_concurrency=1, budget_policy={})
        instance = AgentInstance(tenant_id=customer.id, agent_definition_id=definition.id, agent_template_id=template.id, sponsor_user_id=owner.id, name="Live Git Branch Certification Instance", configuration={FINGERPRINT_KEY: fingerprint}, permission_policy=permission_policy, approval_policy={}, risk_tier=0, max_concurrency=1, budget_policy={}, enabled=True)
        db.add(instance); await db.flush()
        identity = AgentIdentity(tenant_id=customer.id, agent_instance_id=instance.id, owner_user_id=owner.id, sponsor_user_id=owner.id, subject=f"agent:{customer.id}:{instance.id}", active=True)
        db.add(identity); await db.flush()
        db.add(AgentAccessReview(tenant_id=customer.id, agent_identity_id=identity.id, reviewer_user_id=reviewer.id, decision=AgentAccessReviewDecision.APPROVED, reason="Controlled W2 live certification"))
        db.add(AgentRuntimeBinding(tenant_id=customer.id, agent_definition_id=definition.id, employee_version_id=version.id, is_active=True))
        run = Run(tenant_id=customer.id, employee_id=employee.id, employee_version_id=version.id, agent_instance_id=instance.id, created_by=owner.id, status="pending", input_data={"purpose":"W2 live git_branch certification", "branch":BRANCH, "source_sha":SOURCE_SHA})
        db.add(run); await db.flush()
        arguments = {"branch_name": BRANCH, "source_sha": SOURCE_SHA}
        approval = ToolApprovalRequest(tenant_id=customer.id, run_id=run.id, tool_name="workforce_git_branch", tool_call_id=f"w2-live-{uuid.uuid4().hex}", arguments=arguments, continuation_messages=[], iteration=0, status="approved", requested_by=owner.id, decided_by=reviewer.id, decision_reason="Controlled W2 live certification; temporary branch only", decided_at=datetime.now(timezone.utc))
        db.add(approval); await db.commit()
        return customer.id, instance.id, run.id, approval.id, approval.tool_call_id

async def execute(tenant_id: uuid.UUID, instance_id: uuid.UUID, run_id: uuid.UUID, approval_id: uuid.UUID, tool_call_id: str) -> dict:
    arguments = {"branch_name": BRANCH, "source_sha": SOURCE_SHA}
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(
            tenant_id=tenant_id, agent_instance_id=instance_id, run_id=run_id
        ):
            result = await registry.execute(
                "workforce_git_branch", arguments,
                permissions={"run.execute"}, db=db, tenant_id=tenant_id,
                agent_instance_id=instance_id, tool_call_id=tool_call_id,
            )
        await db.commit()
    assert result["provider"]["provider"] == "github"
    assert result["provider_execution"] == "executed", result
    assert result["executed"] is True, result
    assert result["approval_required"] is True, result
    assert result["external_side_effect"] is True, result
    print("W2 LIVE GIT BRANCH GOVERNANCE PASS")
    print("W2 LIVE GIT BRANCH PROVIDER WRITE PASS")
    print(f"W2 LIVE GIT BRANCH CREATED {BRANCH}")
    return result


def cleanup() -> None:
    req = Request(
        f"https://api.github.com/repos/{REPO}/git/refs/heads/{BRANCH}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Employee-W2-Live-Certification",
        },
        method="DELETE",
    )
    with urlopen(req, timeout=10) as response:
        if response.status != 204:
            raise AssertionError(f"branch cleanup returned HTTP {response.status}")
    print("W2 LIVE GIT BRANCH CLEANUP PASS")


async def main() -> None:
    assert_branch_absent()
    tenant_id, instance_id, run_id, approval_id, tool_call_id = await prepare()
    await execute(tenant_id, instance_id, run_id, approval_id, tool_call_id)
    cleanup()


if __name__ == "__main__":
    asyncio.run(main())

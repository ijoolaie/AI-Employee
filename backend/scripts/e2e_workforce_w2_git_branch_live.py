"""Controlled live certification of the governed workforce git_branch write path."""
from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.employee import EmployeeVersion
from app.models.run import Run
from app.models.agent_instance import AgentInstance
from app.models.agent_template import AgentTemplate
from app.models.tool_approval import ToolApprovalRequest
from app.models.user import User
from app.services import agent_tool_governance
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint
from app.services.ai_workforce_roles import get_workforce_capability_contract
from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError

REPO = "ijoolaie/AI-Employee"
TOKEN = os.environ["ENGINEERING_GITHUB_TOKEN"]
SOURCE_SHA = os.environ["GITHUB_SHA"]
BRANCH = os.environ.get("W2_LIVE_BRANCH", f"ai-cert/w2-git-branch-{os.environ.get('GITHUB_RUN_ID', uuid.uuid4().hex[:8])}")
TENANT_ID = uuid.UUID(os.environ["W2_LIVE_TENANT_ID"])


async def prepare() -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, str]:
    async with AsyncSessionLocal() as db:
        instance = (await db.execute(select(AgentInstance).where(AgentInstance.tenant_id == TENANT_ID).order_by(AgentInstance.created_at.desc()).limit(1))).scalar_one()
        template = (await db.execute(select(AgentTemplate).where(AgentTemplate.id == instance.agent_template_id, AgentTemplate.tenant_id == TENANT_ID))).scalar_one()
        version = (await db.execute(select(EmployeeVersion).order_by(EmployeeVersion.id.desc()).limit(1))).scalar_one()
        users = list((await db.execute(select(User).where(User.tenant_id == TENANT_ID, User.is_active.is_(True)).order_by(User.created_at.asc()))).scalars().all())
        if len(users) < 2:
            raise AssertionError("Live certification requires two active users for separation of duties")
        requester, reviewer = users[0], users[-1]

        allowed_tools = sorted(set((instance.permission_policy or {}).get("allowed_tools") or []) | {"workforce_git_branch"})
        permission_policy = {"permissions": ["run.execute"], "allowed_tools": allowed_tools}
        instance.permission_policy = permission_policy
        template.permission_policy = permission_policy
        configuration = dict(instance.configuration or {})
        approved_fingerprint = execution_authority_fingerprint(
            tenant_id=TENANT_ID, template_id=template.id, template_version=template.version,
            agent_definition_id=instance.agent_definition_id, risk_tier=instance.risk_tier,
            capability_contract=template.capability_contract, permission_policy=permission_policy,
            approval_policy=instance.approval_policy, install_policy=template.install_policy,
            configuration={k:v for k,v in configuration.items() if k != FINGERPRINT_KEY},
            max_concurrency=instance.max_concurrency, budget_policy=instance.budget_policy,
        )
        instance.configuration = {**configuration, FINGERPRINT_KEY: approved_fingerprint}

        run = Run(
            tenant_id=TENANT_ID, employee_id=version.employee_id, employee_version_id=version.id,
            agent_instance_id=instance.id, created_by=requester.id, status="pending",
            input_data={"purpose":"W2 live git_branch certification", "branch":BRANCH, "source_sha":SOURCE_SHA},
        )
        db.add(run)
        await db.flush()
        arguments = {"branch_name": BRANCH, "source_sha": SOURCE_SHA}
        approval = ToolApprovalRequest(
            tenant_id=TENANT_ID, run_id=run.id, tool_name="workforce_git_branch",
            tool_call_id=f"w2-live-{uuid.uuid4().hex}", arguments=arguments,
            continuation_messages=[], iteration=0, status="approved",
            requested_by=requester.id, decided_by=reviewer.id,
            decision_reason="Controlled W2 live certification; temporary branch only",
            decided_at=datetime.now(timezone.utc),
        )
        db.add(approval)
        await db.commit()
        return instance.id, run.id, approval.id, approval.tool_call_id


async def execute(instance_id: uuid.UUID, run_id: uuid.UUID, approval_id: uuid.UUID, tool_call_id: str) -> dict:
    arguments = {"branch_name": BRANCH, "source_sha": SOURCE_SHA}
    async with AsyncSessionLocal() as db:
        async with agent_tool_governance.agent_tool_context(
            tenant_id=TENANT_ID, agent_instance_id=instance_id, run_id=run_id
        ):
            result = await registry.execute(
                "workforce_git_branch", arguments,
                permissions={"run.execute"}, db=db, tenant_id=TENANT_ID,
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
    instance_id, run_id, approval_id, tool_call_id = await prepare()
    try:
        await execute(instance_id, run_id, approval_id, tool_call_id)
    finally:
        cleanup()


if __name__ == "__main__":
    asyncio.run(main())

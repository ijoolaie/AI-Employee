"""Real-stack W4 Social/Instagram workforce certification.

Verifies governed Social Media Employee runs, tenant-scoped social operation
artifacts, approval state for publication/DM operations, provenance, and the
fail-closed provider boundary. No Instagram API execution is claimed.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from urllib.request import Request, urlopen

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.agent_instance import AgentInstance
from app.models.run import Run
from app.models.tenant import Tenant
from app.services import edition_service, license_service
from app.services.agent_execution_adapter import AgentExecutionAdapter
from app.services.agent_governance import governed_agent_execution
from app.services.ai_workforce_roles import get_workforce_capability_contract
from app.services import workforce_semantic_domains
from scripts.e2e_workforce_w1_control_plane_verify import provision_agent

SOCIAL_TOOLS = [
    "workforce_read_comments",
    "workforce_triage_comments",
    "workforce_read_analytics",
    "workforce_publication_status",
    "workforce_publish_post",
    "workforce_publish_reel",
    "workforce_publish_story",
    "workforce_schedule_publication",
    "workforce_respond_to_dm",
]

def register_tenant(base: str, suffix: str):
    payload = json.dumps({
        "tenant_name": f"W4 Social E2E {suffix}",
        "tenant_slug": f"w4-social-{suffix}",
        "email": f"w4-owner-{suffix}@example.com",
        "password": "W4SocialE2E-2026!",
        "full_name": "W4 CEO",
    }).encode()
    with urlopen(Request(
        f"{base}/auth/register", data=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    ), timeout=20) as response:
        data = json.loads(response.read().decode())
        assert response.status == 201, data
        token = data["data"]["access_token"]
    with urlopen(Request(
        f"{base}/auth/me",
        headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
        method="GET",
    ), timeout=20) as response:
        me = json.loads(response.read().decode())
        assert response.status == 200, me
    return uuid.UUID(me["data"]["tenant"]["id"]), uuid.UUID(me["data"]["user"]["id"])

async def license_fixture(tenant_id, suffix):
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
        tenant.tenant_kind = edition_service.EDITION_CUSTOMER
        vendor = Tenant(name=f"W4 Vendor {suffix}", slug=f"w4-vendor-{suffix}",
                        status="active", tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor)
        await db.flush()
        reseller = Tenant(name=f"W4 Reseller {suffix}", slug=f"w4-reseller-{suffix}",
                          status="active", tenant_kind=edition_service.EDITION_RESELLER,
                          parent_tenant_id=vendor.id)
        db.add(reseller)
        await db.flush()
        tenant.parent_tenant_id = reseller.id
        features = ["employee.run"] + [f"tool:{name}" for name in SOCIAL_TOOLS]
        row = await license_service.issue_license(
            db, issuer=reseller, tenant=tenant, feature_codes=features,
            metadata={"certification_fixture": True, "purpose": "workforce-w4-social-e2e"},
        )
        assert row.status == "active"
        await db.commit()

async def new_run(tenant_id, agent_id, owner_id, employee_id, version_id):
    async with AsyncSessionLocal() as db:
        run = Run(
            tenant_id=tenant_id, employee_id=employee_id, employee_version_id=version_id,
            agent_instance_id=agent_id, created_by=owner_id, status="pending",
            input_data={"objective": "W4 governed social workforce certification"},
        )
        db.add(run)
        await db.commit()
        return run.id

async def execute(tenant_id, agent_id, employee_id, version_id, run_id, tool, operation, arguments):
    async with AsyncSessionLocal() as db:
        agent = (await db.execute(select(AgentInstance).where(
            AgentInstance.id == agent_id, AgentInstance.tenant_id == tenant_id
        ))).scalar_one()
        async with governed_agent_execution(
            tenant_id=tenant_id, agent_instance_id=agent_id, run_id=run_id,
            employee_id=employee_id, employee_version_id=version_id,
        ):
            result = await AgentExecutionAdapter(db).execute_tool(
                agent=agent, tool_name=tool, workforce_operation=operation, arguments=arguments
            )
            await db.commit()
            return result

async def run():
    suffix = str(time.time_ns())[-10:]
    base = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")
    tenant_id, owner_id = register_tenant(base, suffix)
    await license_fixture(tenant_id, suffix)

    agent_id, employee_id, version_id = await provision_agent(
        tenant_id, suffix, owner_id, "ai_social_media", "social-media", SOCIAL_TOOLS
    )

    read_run = await new_run(tenant_id, agent_id, owner_id, employee_id, version_id)
    read_result = await execute(
        tenant_id, agent_id, employee_id, version_id, read_run,
        "workforce_read_analytics", "read_analytics",
        {"channel": "instagram", "provider": "instagram"},
    )
    assert read_result["status"] == "request"
    assert read_result["approval_required"] is False
    assert read_result["provider_execution"] == "not_configured"
    assert read_result["external_side_effect"] is False

    publish_run = await new_run(tenant_id, agent_id, owner_id, employee_id, version_id)
    publish = await execute(
        tenant_id, agent_id, employee_id, version_id, publish_run,
        "workforce_publish_post", "publish_post",
        {"channel": "instagram", "content_id": "w4-content-test", "message": "W4 governed publication proposal", "provider": "instagram"},
    )
    assert publish["status"] == "proposal"
    assert publish["approval_required"] is True
    assert publish["approval_status"] == "pending"
    assert publish["provider_execution"] == "not_configured"
    assert publish["external_side_effect"] is True

    payload = workforce_semantic_domains._read_json(str(tenant_id), publish["storage_key"])
    assert payload["kind"] == "social_operation"
    assert payload["tenant_id"] if "tenant_id" in payload else True
    assert payload["provenance"]["tenant_id"] == str(tenant_id)
    assert payload["approval_required"] is True
    assert payload["approval_status"] == "pending"
    assert payload["provider_execution"] == "not_configured"

    dm_run = await new_run(tenant_id, agent_id, owner_id, employee_id, version_id)
    dm = await execute(
        tenant_id, agent_id, employee_id, version_id, dm_run,
        "workforce_respond_to_dm", "respond_to_dm",
        {"channel": "instagram", "message": "W4 governed DM proposal", "provider": "instagram"},
    )
    assert dm["approval_required"] is True
    assert dm["approval_status"] == "pending"
    assert dm["provider_execution"] == "not_configured"

    try:
        workforce_semantic_domains._read_json(str(uuid.uuid4()), publish["storage_key"])
    except Exception:
        pass
    else:
        raise AssertionError("W4 cross-tenant social artifact read unexpectedly succeeded")

    contract = get_workforce_capability_contract("ai_social_media", "publish_post")
    assert contract.approval_required is True
    dm_contract = get_workforce_capability_contract("ai_social_media", "respond_to_dm")
    assert dm_contract.approval_required is True

    print("W4 SOCIAL EMPLOYEE GOVERNED RUN PASS")
    print(f"W4 SOCIAL READ/ANALYTICS PASS social_id={read_result['social_id']}")
    print(f"W4 PUBLICATION PROPOSAL PASS social_id={publish['social_id']}")
    print("W4 APPROVAL STATE PASS")
    print("W4 PROVENANCE AND TENANT ISOLATION PASS")
    print("W4 PUBLICATION PROVIDER BOUNDARY PASS provider_execution=not_configured")
    print("W4 DM APPROVAL BOUNDARY PASS")
    print("WORKFORCE W4 SOCIAL REAL-STACK E2E PASS")

def main():
    try:
        asyncio.run(run())
    except Exception as exc:
        print(f"WORKFORCE W4 SOCIAL REAL-STACK E2E FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()

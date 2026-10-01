"""Real-stack W3 Content & Creative workforce certification.

Exercises Content Producer and Graphic Designer through canonical governed Runs,
then verifies durable artifacts, provenance, approval state, and tenant isolation.
Creative provider execution must remain explicitly unconfigured.
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

CONTENT_TOOLS = ["workforce_produce_article", "workforce_produce_social_caption"]
CREATIVE_TOOLS = ["workforce_create_visual_asset", "workforce_revise_visual_asset"]


def register_tenant(base, suffix):
    payload = json.dumps({
        "tenant_name": f"W3 Content Creative E2E {suffix}",
        "tenant_slug": f"w3-content-creative-{suffix}",
        "email": f"w3-owner-{suffix}@example.com",
        "password": "W3ContentCreativeE2E-2026!",
        "full_name": "W3 CEO",
    }).encode()
    with urlopen(Request(
        f"{base}/auth/register", data=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    ), timeout=20) as response:
        data = json.loads(response.read().decode())
        assert response.status == 201, data
        return uuid.UUID(data["data"]["tenant"]["id"]), uuid.UUID(data["data"]["user"]["id"])


async def license_fixture(tenant_id, suffix):
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
        tenant.tenant_kind = edition_service.EDITION_CUSTOMER
        vendor = Tenant(name=f"W3 Vendor {suffix}", slug=f"w3-vendor-{suffix}", status="active", tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor)
        await db.flush()
        reseller = Tenant(name=f"W3 Reseller {suffix}", slug=f"w3-reseller-{suffix}", status="active", tenant_kind=edition_service.EDITION_RESELLER, parent_tenant_id=vendor.id)
        db.add(reseller)
        await db.flush()
        tenant.parent_tenant_id = reseller.id
        features = ["employee.run"] + [f"tool:{n}" for n in CONTENT_TOOLS + CREATIVE_TOOLS]
        row = await license_service.issue_license(db, issuer=reseller, tenant=tenant, feature_codes=features,
            metadata={"certification_fixture": True, "purpose": "workforce-w3-content-creative-e2e"})
        assert row.status == "active"
        await db.commit()


async def new_run(tenant_id, agent_id, owner_id, employee_id, version_id):
    async with AsyncSessionLocal() as db:
        run = Run(tenant_id=tenant_id, employee_id=employee_id, employee_version_id=version_id,
                  agent_instance_id=agent_id, created_by=owner_id, status="pending",
                  input_data={"objective": "W3 governed content and creative certification"})
        db.add(run)
        await db.commit()
        return run.id


async def execute(tenant_id, agent_id, employee_id, version_id, run_id, tool, operation, arguments):
    async with AsyncSessionLocal() as db:
        agent = (await db.execute(select(AgentInstance).where(
            AgentInstance.id == agent_id, AgentInstance.tenant_id == tenant_id))).scalar_one()
        async with governed_agent_execution(tenant_id=tenant_id, agent_instance_id=agent_id, run_id=run_id,
                                             employee_id=employee_id, employee_version_id=version_id):
            result = await AgentExecutionAdapter(db).execute_tool(
                agent=agent, tool_name=tool, workforce_operation=operation, arguments=arguments)
            await db.commit()
            return result


async def run():
    suffix = str(time.time_ns())[-10:]
    base = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")
    tenant_id, owner_id = register_tenant(base, suffix)
    await license_fixture(tenant_id, suffix)

    content_agent, content_employee, content_version = await provision_agent(
        tenant_id, suffix, owner_id, "ai_content_producer", "content-producer", CONTENT_TOOLS)
    creative_agent, creative_employee, creative_version = await provision_agent(
        tenant_id, suffix, owner_id, "ai_graphic_designer", "graphic-designer", CREATIVE_TOOLS)

    article_run = await new_run(tenant_id, content_agent, owner_id, content_employee, content_version)
    article = await execute(tenant_id, content_agent, content_employee, content_version, article_run,
        "workforce_produce_article", "produce_article",
        {"title": "W3 certification article", "body": "Deterministic governed content artifact.", "metadata": {"source": "w3-e2e"}})
    assert article["status"] == "draft"
    assert article["provider_execution"] == "not_required"
    assert article["approval_required"] is False

    caption_run = await new_run(tenant_id, content_agent, owner_id, content_employee, content_version)
    caption = await execute(tenant_id, content_agent, content_employee, content_version, caption_run,
        "workforce_produce_social_caption", "produce_social_caption",
        {"title": "W3 caption", "body": "Governed caption variant.", "metadata": {"source": "w3-e2e"}})
    assert caption["content_id"] != article["content_id"]
    assert caption["storage_key"] != article["storage_key"]

    creative_run = await new_run(tenant_id, creative_agent, owner_id, creative_employee, creative_version)
    creative = await execute(tenant_id, creative_agent, creative_employee, creative_version, creative_run,
        "workforce_create_visual_asset", "create_visual_asset",
        {"prompt": "A clean abstract SaaS launch visual", "brand_context": "W3 test brand", "provider": "image-provider"})
    assert creative["status"] == "draft"
    assert creative["provider_execution"] == "not_configured"

    article_payload = workforce_semantic_domains._read_json(str(tenant_id), article["storage_key"])
    creative_payload = workforce_semantic_domains._read_json(str(tenant_id), creative["storage_key"])
    assert article_payload["provenance"]["tenant_id"] == str(tenant_id)
    assert creative_payload["provenance"]["tenant_id"] == str(tenant_id)
    assert article_payload["approval_status"] == "not_required"
    assert creative_payload["approval_status"] == "not_required"
    assert creative_payload["provider_execution"] == "not_configured"

    try:
        workforce_semantic_domains._read_json(str(uuid.uuid4()), article["storage_key"])
    except Exception:
        pass
    else:
        raise AssertionError("W3 cross-tenant artifact read unexpectedly succeeded")

    contract = get_workforce_capability_contract("ai_content_producer", "external_content_commitment")
    assert contract.approval_required is True

    print("W3 CONTENT EMPLOYEE GOVERNED RUN PASS")
    print(f"W3 CONTENT ARTIFACT PASS content_id={article['content_id']}")
    print("W3 CREATIVE EMPLOYEE GOVERNED RUN PASS")
    print(f"W3 CREATIVE REQUEST PASS asset_id={creative['asset_id']}")
    print("W3 PROVENANCE AND TENANT ISOLATION PASS")
    print("W3 APPROVAL STATE PASS")
    print("W3 APPROVAL CONTRACT PASS external_content_commitment=human_approval_required")
    print("W3 CREATIVE PROVIDER BOUNDARY PASS provider_execution=not_configured")
    print("WORKFORCE W3 CONTENT-CREATIVE REAL-STACK E2E PASS")


def main():
    try:
        asyncio.run(run())
    except Exception as exc:
        print(f"WORKFORCE W3 CONTENT-CREATIVE REAL-STACK E2E FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

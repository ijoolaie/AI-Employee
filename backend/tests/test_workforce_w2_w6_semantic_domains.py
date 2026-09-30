import pytest

from app.services.ai_workforce_roles import get_workforce_capability_contract, get_workforce_role
from app.services.workforce_semantic_domains import execute_engineering, execute_sales, execute_social, execute_website


@pytest.mark.asyncio
async def test_w2_engineering_workspace_is_tenant_scoped():
    created = await execute_engineering(
        {"_operation": "workspace_create_file", "path": "src/app.py", "content": "print('ok')"},
        tenant_id="tenant-a",
    )
    assert created["path"] == "src/app.py"
    assert created["storage_key"].startswith("tenant-a/")


@pytest.mark.asyncio
async def test_w2_engineering_external_delivery_is_proposal_only():
    result = await execute_engineering({"_operation": "deploy_proposal"}, tenant_id="tenant-a")
    assert result["status"] == "proposal"
    assert result["approval_required"] is True


@pytest.mark.asyncio
async def test_w3_creative_and_content_bindings_exist():
    graphic = get_workforce_role("ai_graphic_designer")
    assert get_workforce_capability_contract(graphic.code, "create_visual_asset").tool_names == ("workforce_create_visual_asset",)
    content = get_workforce_role("ai_content_producer")
    assert get_workforce_capability_contract(content.code, "produce_article").tool_names == ("workforce_produce_article",)


@pytest.mark.asyncio
async def test_w4_social_external_actions_are_approval_gated():
    role = get_workforce_role("ai_social_media")
    assert "publish_post" in role.approval_required_operations
    result = await execute_social({"_operation": "publish_post", "channel": "instagram"}, tenant_id="tenant-a")
    assert result["approval_required"] is True
    assert result["external_side_effect"] is True


@pytest.mark.asyncio
async def test_w5_sales_outreach_is_proposal_only():
    result = await execute_sales({"_operation": "prepare_outreach_draft", "query": "B2B SaaS"}, tenant_id="tenant-a")
    assert result["status"] == "proposal"
    assert result["approval_required"] is True


@pytest.mark.asyncio
async def test_w6_website_deploy_and_rollback_are_approval_gated():
    role = get_workforce_role("ai_website_employee")
    assert "website_deploy" in role.approval_required_operations
    deploy = await execute_website({"_operation": "website_deploy", "site": "internal-company"}, tenant_id="tenant-a")
    rollback = await execute_website({"_operation": "website_rollback", "site": "internal-company"}, tenant_id="tenant-a")
    assert deploy["approval_required"] is True
    assert rollback["approval_required"] is True

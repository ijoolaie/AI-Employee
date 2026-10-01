import pytest

from app.ai.tool_registry import registry
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
async def test_w3_content_artifacts_are_unique_versioned_and_tenant_scoped():
    from app.services.workforce_semantic_domains import execute_content

    first = await execute_content(
        {
            "_operation": "produce_article",
            "title": "First",
            "body": "A",
            "metadata": {"campaign": "w3"},
        },
        tenant_id="tenant-a",
    )
    second = await execute_content(
        {
            "_operation": "produce_article",
            "title": "Second",
            "body": "B",
            "metadata": {"campaign": "w3"},
        },
        tenant_id="tenant-a",
    )
    assert first["content_id"] != second["content_id"]
    assert first["storage_key"] != second["storage_key"]
    assert first["version"] == 1
    assert first["status"] == "draft"
    assert first["approval_required"] is False
    assert first["approval_status"] == "not_required"
    assert first["storage_key"].startswith("tenant-a/")

    other_tenant = await execute_content(
        {
            "_operation": "produce_social_caption",
            "title": "Other",
            "body": "Tenant B",
        },
        tenant_id="tenant-b",
    )
    assert other_tenant["storage_key"].startswith("tenant-b/")
    assert other_tenant["storage_key"] != first["storage_key"]


@pytest.mark.asyncio
async def test_w3_creative_requests_are_unique_and_never_claim_provider_execution():
    from app.services.workforce_semantic_domains import execute_creative

    first = await execute_creative(
        {
            "_operation": "create_visual_asset",
            "prompt": "A product hero image",
            "brand_context": "W3 test",
            "provider": "paid-provider",
        },
        tenant_id="tenant-a",
    )
    second = await execute_creative(
        {
            "_operation": "revise_visual_asset",
            "prompt": "A revised product hero image",
            "brand_context": "W3 test",
        },
        tenant_id="tenant-a",
    )
    assert first["asset_id"] != second["asset_id"]
    assert first["storage_key"] != second["storage_key"]
    assert first["version"] == 1
    assert first["status"] == "draft"
    assert first["provider_execution"] == "not_configured"
    assert first["approval_required"] is False
    assert first["approval_status"] == "not_required"
    assert first["storage_key"].startswith("tenant-a/")


@pytest.mark.asyncio
async def test_w4_social_external_actions_are_approval_gated():
    role = get_workforce_role("ai_social_media")
    assert "publish_post" in role.approval_required_operations
    result = await execute_social({"_operation": "publish_post", "channel": "instagram"}, tenant_id="tenant-a")
    assert result["approval_required"] is True
    assert result["external_side_effect"] is True
    connect = await execute_social({"_operation": "connect_channel", "channel": "instagram"}, tenant_id="tenant-a")
    assert connect["approval_required"] is True
    assert connect["external_side_effect"] is True


@pytest.mark.asyncio
async def test_w5_sales_outreach_draft_is_non_external():
    result = await execute_sales({"_operation": "prepare_outreach_draft", "query": "B2B SaaS"}, tenant_id="tenant-a")
    assert result["status"] == "draft_or_report"
    assert result["external_side_effect"] is False


@pytest.mark.asyncio
async def test_w6_website_deploy_and_rollback_are_approval_gated():
    role = get_workforce_role("ai_website_employee")
    assert "website_deploy" in role.approval_required_operations
    deploy = await execute_website({"_operation": "website_deploy", "site": "internal-company"}, tenant_id="tenant-a")
    rollback = await execute_website({"_operation": "website_rollback", "site": "internal-company"}, tenant_id="tenant-a")
    assert deploy["approval_required"] is True
    assert rollback["approval_required"] is True


def test_w2_w6_all_explicitly_bound_tools_are_registered():
    roles = [
        "ai_graphic_designer", "ai_software_developer", "ai_content_producer",
        "ai_social_media", "ai_sales_lead_generation", "ai_website_employee",
    ]
    registered = {tool.name for tool in registry.list()}
    for role_code in roles:
        role = get_workforce_role(role_code)
        for contract in role.capability_contract:
            for tool_name in contract.tool_names:
                assert tool_name in registered, (role_code, contract.operation, tool_name)


def test_w4_w6_external_actions_are_approval_gated_at_registry():
    for tool_name in (
        "workforce_connect_channel", "workforce_publish_post", "workforce_publish_reel",
        "workforce_publish_story", "workforce_schedule_publication", "workforce_respond_to_dm",
        "workforce_website_deploy", "workforce_website_rollback",
    ):
        tool = registry.get(tool_name)
        assert tool.requires_approval is True
        assert tool.external_side_effects is True


@pytest.mark.asyncio
async def test_w2_provider_bound_operations_never_claim_execution():
    for operation in ("workspace_test", "workspace_lint", "workspace_build", "git_branch", "git_pr_proposal", "ci_status", "health_check"):
        result = await execute_engineering({"_operation": operation}, tenant_id="tenant-a")
        assert result["provider_execution"] == "not_configured"
        assert result["requires_provider"] or result["provider_required"]


@pytest.mark.asyncio
async def test_w5_provider_boundary_is_explicit():
    research = await execute_sales({"_operation": "lead_research", "query": "SaaS"}, tenant_id="tenant-a")
    outreach = await execute_sales({"_operation": "prepare_outreach_draft", "query": "SaaS"}, tenant_id="tenant-a")
    assert research["provider_execution"] == "not_configured"
    assert outreach["provider_execution"] == "not_configured"
    assert outreach["external_side_effect"] is False

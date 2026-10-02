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


@pytest.mark.asyncio
async def test_w4_social_operations_are_unique_tenant_scoped_and_provider_bound():
    from app.services.workforce_semantic_domains import execute_social, _read_json

    proposal = await execute_social(
        {
            "_operation": "publish_post",
            "channel": "instagram",
            "content_id": "content-123",
            "provider": "instagram",
        },
        tenant_id="tenant-a",
    )
    read_request = await execute_social(
        {
            "_operation": "read_comments",
            "channel": "instagram",
        },
        tenant_id="tenant-a",
    )
    assert proposal["social_id"] != read_request["social_id"]
    assert proposal["storage_key"].startswith("tenant-a/")
    assert read_request["storage_key"].startswith("tenant-a/")
    assert proposal["status"] == "proposal"
    assert proposal["approval_required"] is True
    assert proposal["approval_status"] == "pending"
    assert proposal["external_side_effect"] is True
    assert proposal["provider_execution"] == "not_configured"
    assert read_request["status"] == "request"
    assert read_request["approval_required"] is False
    assert read_request["provider_execution"] == "not_configured"

    payload = _read_json("tenant-a", proposal["storage_key"])
    assert payload["provenance"]["tenant_id"] == "tenant-a"
    assert payload["provider_execution"] == "not_configured"
    assert payload["approval_status"] == "pending"

    with pytest.raises(Exception):
        _read_json("tenant-b", proposal["storage_key"])


def test_w4_social_registry_dispatch_matches_operation():
    expected = {
        "workforce_connect_channel": "connect_channel",
        "workforce_read_comments": "read_comments",
        "workforce_triage_comments": "triage_comments",
        "workforce_read_analytics": "read_analytics",
        "workforce_publication_status": "publication_status",
        "workforce_publish_post": "publish_post",
        "workforce_publish_reel": "publish_reel",
        "workforce_publish_story": "publish_story",
        "workforce_schedule_publication": "schedule_publication",
        "workforce_respond_to_dm": "respond_to_dm",
    }
    for tool_name, operation in expected.items():
        tool = registry.get(tool_name)
        assert tool is not None
        assert operation in tool.description


@pytest.mark.asyncio
async def test_w5_sales_artifacts_are_tenant_scoped_and_external_outreach_is_proposed():
    from app.services.workforce_semantic_domains import execute_sales, _read_json

    research = await execute_sales(
        {"_operation": "lead_research", "query": "B2B SaaS"},
        tenant_id="tenant-a",
    )
    outreach = await execute_sales(
        {"_operation": "external_outreach", "query": "B2B SaaS"},
        tenant_id="tenant-a",
    )
    assert research["sales_id"] != outreach["sales_id"]
    assert research["status"] == "draft_or_report"
    assert research["provider_execution"] == "not_configured"
    assert research["external_side_effect"] is False
    assert outreach["status"] == "proposal"
    assert outreach["approval_required"] is True
    assert outreach["approval_status"] == "approved"
    assert outreach["external_side_effect"] is True
    assert outreach["provider_execution"] == "not_configured"
    assert outreach["storage_key"].startswith("tenant-a/")

    payload = _read_json("tenant-a", outreach["storage_key"])
    assert payload["provenance"]["tenant_id"] == "tenant-a"
    with pytest.raises(Exception):
        _read_json("tenant-b", outreach["storage_key"])


@pytest.mark.asyncio
async def test_w6_website_changes_are_unique_and_provider_bound():
    from app.services.workforce_semantic_domains import execute_website, _read_json

    first = await execute_website(
        {"_operation": "website_requirements", "site": "internal-company", "spec": {"page": "home"}},
        tenant_id="tenant-a",
    )
    deploy = await execute_website(
        {"_operation": "website_deploy", "site": "internal-company", "spec": {"release": "w6"}},
        tenant_id="tenant-a",
    )
    assert first["change_id"] != deploy["change_id"]
    assert first["storage_key"] != deploy["storage_key"]
    assert first["status"] == "staged"
    assert first["approval_required"] is False
    assert first["provider_execution"] == "not_configured"
    assert deploy["status"] == "proposal"
    assert deploy["approval_required"] is True
    assert deploy["approval_status"] == "pending"
    assert deploy["external_side_effect"] is True
    assert deploy["provider_execution"] == "not_configured"
    payload = _read_json("tenant-a", deploy["storage_key"])
    assert payload["provenance"]["tenant_id"] == "tenant-a"
    with pytest.raises(Exception):
        _read_json("tenant-b", deploy["storage_key"])

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
async def test_w2_engineering_workspace_paths_cannot_collide_after_key_normalization():
    from app.services.workforce_semantic_domains import _read_json

    first = await execute_engineering(
        {"_operation": "workspace_create_file", "path": "src/app.py", "content": "first"},
        tenant_id="tenant-collision",
    )
    second = await execute_engineering(
        {"_operation": "workspace_create_file", "path": "src_app.py", "content": "second"},
        tenant_id="tenant-collision",
    )

    assert first["storage_key"] != second["storage_key"]
    assert _read_json("tenant-collision", first["storage_key"])["content"] == "first"
    assert _read_json("tenant-collision", second["storage_key"])["content"] == "second"


@pytest.mark.asyncio
async def test_software_developer_workspace_acceptance_checks_lifecycle_and_isolation():
    from app.services.workforce_semantic_domains import run_software_developer_workspace_acceptance

    tenant_id = "tenant-workspace-acceptance"
    result = await run_software_developer_workspace_acceptance(tenant_id=tenant_id)

    assert result["suite_id"] == "software_developer_workspace_acceptance"
    assert result["suite_version"] == "workspace_artifact_lifecycle_v1"
    assert result["status"] == "passed"
    assert result["checks_passed"] == 10
    assert all(check["passed"] for check in result["checks"])
    assert result["evidence_boundary"] == "local_workspace_artifact_only"
    assert result["provider_execution"] == "not_required"
    assert result["external_side_effects"] is False

    from app.services.storage import get_storage_backend
    backend = get_storage_backend()
    assert not any(
        "workspace-lifecycle-" in key
        for key in backend.list_prefix(f"{tenant_id}/")
    )


@pytest.mark.asyncio
async def test_software_developer_workspace_acceptance_cleans_up_after_failure(monkeypatch):
    from app.services import workforce_semantic_domains as domains
    from app.services.storage import get_storage_backend
    from app.core.exceptions import ValidationAppError

    original = domains.execute_engineering
    created_keys = []

    async def fail_after_create(arguments, **context):
        if arguments.get("_operation") == "workspace_create_file":
            result = await original(arguments, **context)
            created_keys.append(result["storage_key"])
            return result
        if arguments.get("_operation") == "workspace_read":
            raise ValidationAppError("injected acceptance failure")
        return await original(arguments, **context)

    monkeypatch.setattr(domains, "execute_engineering", fail_after_create)
    tenant_id = "tenant-workspace-acceptance-failure"
    with pytest.raises(ValidationAppError, match="injected acceptance failure"):
        await domains.run_software_developer_workspace_acceptance(tenant_id=tenant_id)

    assert len(created_keys) == 1
    assert not get_storage_backend().exists(created_keys[0])


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



@pytest.mark.asyncio
async def test_w3_content_qa_runs_deterministic_checks_and_persists_tenant_scoped_report():
    from app.services.workforce_semantic_domains import _read_json, execute_content

    passed = await execute_content(
        {
            "_operation": "content_qa",
            "title": "Launch announcement",
            "body": "We are launching the new dashboard today. Explore the updated workflow and share feedback.",
            "metadata": {"stage": "qa"},
        },
        tenant_id="tenant-qa",
    )
    assert passed["status"] == "passed"
    assert all(check["passed"] for check in passed["checks"])
    assert passed["findings"] == []
    assert passed["provider_execution"] == "not_required"
    assert passed["storage_key"].startswith("tenant-qa/")
    persisted = _read_json("tenant-qa", passed["storage_key"])
    assert persisted["kind"] == "content_qa_report"
    assert persisted["provenance"]["tenant_id"] == "tenant-qa"
    assert "Does not assess factual accuracy, tone, brand compliance, or legal compliance." in persisted["limitations"]

    needs_revision = await execute_content(
        {
            "_operation": "content_qa",
            "title": "",
            "body": "Draft placeholder: TODO replace this text with final copy.",
        },
        tenant_id="tenant-qa",
    )
    assert needs_revision["status"] == "needs_revision"
    assert {finding["check_id"] for finding in needs_revision["findings"]} == {
        "title_present", "placeholder_text_absent"
    }
    with pytest.raises(Exception):
        _read_json("another-tenant", passed["storage_key"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    [
        "lead_research",
        "lead_qualification",
        "crm_enrichment",
        "prepare_outreach_draft",
        "prepare_follow_up_queue",
        "prepare_proposal",
        "prepare_meeting_request",
        "pipeline_reporting",
        "conversion_attribution",
    ],
)
async def test_w5_sales_routine_operations_are_artifacts_not_provider_execution(operation):
    """Prevent routine sales artifacts from being mistaken for live source-backed work."""
    from app.services.workforce_semantic_domains import _read_json

    result = await execute_sales(
        {
            "_operation": operation,
            "query": "B2B SaaS",
            "criteria": {"industry": "software"},
        },
        tenant_id="tenant-sales-a",
    )

    assert result["operation"] == operation
    assert result["status"] == "draft_or_report"
    assert result["provider_execution"] == "not_configured"
    assert result["external_side_effect"] is False
    assert result["storage_key"].startswith("tenant-sales-a/")

    payload = _read_json("tenant-sales-a", result["storage_key"])
    assert payload["kind"] == "sales_operation"
    assert payload["operation"] == operation
    assert payload["provider_execution"] == "not_configured"
    assert payload["external_side_effect"] is False
    assert payload["provenance"]["tenant_id"] == "tenant-sales-a"

    with pytest.raises(Exception):
        _read_json("tenant-sales-b", result["storage_key"])


@pytest.mark.asyncio
async def test_w5_lead_qualification_scores_only_explicit_signals_and_persists_explanation():
    from app.services.workforce_semantic_domains import _read_json

    qualified = await execute_sales(
        {
            "_operation": "lead_qualification",
            "query": "Example B2B lead",
            "criteria": {
                "industry_match": True,
                "need_confirmed": True,
                "budget_confirmed": True,
                "decision_maker_identified": True,
                "timeline_confirmed": False,
            },
        },
        tenant_id="tenant-sales-qualification",
    )
    report = qualified["qualification"]
    assert report["method"] == "explicit_boolean_signals_v1"
    assert report["score"] == 80
    assert report["status"] == "qualified"
    assert report["passed_signals"] == [
        "industry_match", "need_confirmed", "budget_confirmed", "decision_maker_identified"
    ]
    assert report["missing_or_unconfirmed_signals"] == ["timeline_confirmed"]
    persisted = _read_json("tenant-sales-qualification", qualified["storage_key"])
    assert persisted["qualification"] == report
    assert persisted["provider_execution"] == "not_configured"
    assert persisted["external_side_effect"] is False

    insufficient = await execute_sales(
        {"_operation": "lead_qualification", "criteria": {}},
        tenant_id="tenant-sales-qualification",
    )
    assert insufficient["qualification"]["score"] == 0
    assert insufficient["qualification"]["status"] == "insufficient_evidence"
    assert len(insufficient["qualification"]["missing_or_unconfirmed_signals"]) == 5

    with pytest.raises(Exception):
        _read_json("other-tenant", qualified["storage_key"])


@pytest.mark.asyncio
async def test_w6_website_health_check_persists_read_only_tenant_scoped_evidence(monkeypatch):
    from app.services import workforce_website_health_provider
    from app.services.workforce_semantic_domains import _read_json

    monkeypatch.setattr(
        workforce_website_health_provider,
        "check_website_health",
        lambda *, tenant_id, site: {
            "site": site,
            "provider_execution": "read_verified",
            "healthy": True,
            "status_code": 200,
            "content_type": "text/html",
            "checked_at": "2026-10-14T00:00:00+00:00",
            "reason": "HTTP health check completed",
        },
    )
    result = await execute_website(
        {"_operation": "website_health_check", "site": "primary"},
        tenant_id="tenant-a",
    )
    assert result["status"] == "healthy"
    assert result["provider_execution"] == "read_verified"
    assert result["external_side_effect"] is False
    assert result["approval_required"] is False
    assert result["health_check"]["status_code"] == 200

    payload = _read_json("tenant-a", result["storage_key"])
    assert payload["provenance"]["tenant_id"] == "tenant-a"
    assert payload["health_check"]["healthy"] is True
    assert payload["external_side_effect"] is False
    with pytest.raises(Exception, match="Cross-tenant"):
        _read_json("tenant-b", result["storage_key"])


@pytest.mark.asyncio
async def test_w6_website_health_check_stays_fail_closed_without_provider_configuration():
    result = await execute_website(
        {"_operation": "website_health_check", "site": "primary"},
        tenant_id="tenant-no-config",
    )
    assert result["status"] == "staged"
    assert result["provider_execution"] == "not_configured"
    assert result["external_side_effect"] is False
    assert result["health_check"]["healthy"] is None

@pytest.mark.asyncio
async def test_w2_engineering_delete_missing_workspace_artifact_is_not_reported_as_success():
    import uuid

    from app.core.exceptions import ValidationAppError

    missing_key = f"tenant-a/missing-workspace-{uuid.uuid4().hex}.json"

    with pytest.raises(ValidationAppError, match="Workspace artifact not found"):
        await execute_engineering(
            {
                "_operation": "workspace_delete_file",
                "storage_key": missing_key,
            },
            tenant_id="tenant-a",
        )

@pytest.mark.asyncio
async def test_w2_engineering_edit_rejects_non_workspace_artifacts_without_mutating_them():
    from app.core.exceptions import ValidationAppError
    from app.services.workforce_semantic_domains import _read_json

    change_set = await execute_engineering(
        {
            "_operation": "workspace_change_set",
            "title": "Protected change set",
            "changes": [{"path": "src/app.py", "content": "safe"}],
        },
        tenant_id="tenant-edit-guard",
    )
    original = _read_json("tenant-edit-guard", change_set["storage_key"])

    with pytest.raises(ValidationAppError, match="Artifact is not a workspace file"):
        await execute_engineering(
            {
                "_operation": "workspace_edit_file",
                "storage_key": change_set["storage_key"],
                "content": "tampered",
            },
            tenant_id="tenant-edit-guard",
        )

    assert _read_json("tenant-edit-guard", change_set["storage_key"]) == original

@pytest.mark.asyncio
async def test_w2_engineering_delete_rejects_non_workspace_artifacts_without_deleting_them():
    from app.core.exceptions import ValidationAppError
    from app.services.workforce_semantic_domains import _read_json

    change_set = await execute_engineering(
        {
            "_operation": "workspace_change_set",
            "title": "Protected change set",
            "changes": [{"path": "src/app.py", "content": "safe"}],
        },
        tenant_id="tenant-delete-guard",
    )
    original = _read_json("tenant-delete-guard", change_set["storage_key"])

    with pytest.raises(ValidationAppError, match="Artifact is not a workspace file"):
        await execute_engineering(
            {
                "_operation": "workspace_delete_file",
                "storage_key": change_set["storage_key"],
            },
            tenant_id="tenant-delete-guard",
        )

    assert _read_json("tenant-delete-guard", change_set["storage_key"]) == original


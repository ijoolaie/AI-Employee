import pytest

from app.ai.prompt_assembly import ExecutionContext, assemble_employee_prompt
from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError


def test_registry_contains_controlled_initial_tools():
    names = {tool.name for tool in registry.list()}
    # Phase 2 added `analyze_dataset` (Report Employee) — see
    # documents/58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md
    # Phase 5 added `analyze_document` (Document Employee) — see
    # documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md
    # Phase 2: analyze_dataset (Report)
    # Phase 5: analyze_document (Document)
    # Phase 7: invoice tools (BusinessInvoice) — see
    # documents/67_PHASE_7_INVOICE_EMPLOYEE_AS_BUILT_v0.7.0.md
    assert names == {
        "calculator", "current_time", "send_email", "analyze_dataset", "analyze_document",
        "create_invoice", "update_invoice_status", "analyze_invoice_file", "export_invoice_pdf",
        "invoice_financial_summary", "create_order", "update_order_status", "analyze_order_file",
        "order_summary", "link_order_invoice", "create_deal", "update_deal_stage",
        "sales_pipeline_summary", "sales_forecast", "search_products", "get_product",
        "check_inventory", "get_order", "track_order", "workforce_market_research", "workforce_market_risk_analysis", "workforce_market_trading_plan", "workforce_prepare_ceo_report", "workforce_prepare_growth_report", "workforce_draft_campaign_plan", "workforce_coordinate_content", "workforce_request_capacity",
    }
    assert registry.get("send_email").side_effects is True
    assert registry.get("send_email").requires_approval is True
    assert registry.get("analyze_dataset").requires_approval is False
    assert registry.get("analyze_document").requires_approval is False
    assert registry.get("analyze_document").required_permission == "run.execute"
    assert registry.get("analyze_dataset").required_permission == "run.execute"
    assert registry.get("create_invoice").side_effects is True
    assert registry.get("export_invoice_pdf").side_effects is True
    assert registry.get("invoice_financial_summary").required_permission == "run.execute"


def test_allowed_tools_become_provider_definitions():
    assembly = assemble_employee_prompt(
        prompt_template="You are a calculator employee.", prompt_version="1",
        context=ExecutionContext(input_data={}), allowed_tools=["calculator"],
    )
    assert [tool.name for tool in assembly.tools] == ["calculator"]
    assert assembly.metadata["tool_count"] == 1


def test_unknown_allowed_tool_fails_closed():
    with pytest.raises(ValidationAppError):
        assemble_employee_prompt(prompt_template="test", prompt_version="1", context=ExecutionContext(input_data={}), allowed_tools=["not_registered"])


@pytest.mark.asyncio
async def test_calculator_is_safe_and_schema_validated():
    result = await registry.execute("calculator", {"expression": "(12 + 3) * 2"}, permissions={"run.execute"})
    assert result["result"] == 30
    with pytest.raises(ValidationAppError):
        await registry.execute("calculator", {"expression": "__import__('os').system('whoami')"}, permissions={"run.execute"})


@pytest.mark.asyncio
async def test_current_time_returns_utc():
    result = await registry.execute("current_time", {}, permissions={"run.execute"})
    assert result["utc"].endswith("+00:00")


def test_tool_policy_is_explicit_and_fail_closed():
    calculator = registry.get("calculator")
    assert calculator.required_permission == "run.execute"
    assert calculator.requires_approval is False


@pytest.mark.asyncio
async def test_tool_permission_is_enforced():
    with pytest.raises(ValidationAppError):
        await registry.execute("calculator", {"expression": "2+2"}, permissions=set())


@pytest.mark.asyncio
async def test_approval_required_tool_is_fail_closed_until_approved():
    from app.ai.tool_registry import RegisteredTool
    name = "_test_approval_tool"
    registry.register(RegisteredTool(
        name=name, description="test gated tool",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=lambda _: {"ok": True}, side_effects=False,
        required_permission="run.execute", requires_approval=True,
    ))
    try:
        with pytest.raises(ValidationAppError):
            await registry.execute(name, {}, permissions={"run.execute"}, approval_granted=False)
        result = await registry.execute(name, {}, permissions={"run.execute"}, approval_granted=True)
        assert result == {"ok": True}
    finally:
        registry._tools.pop(name, None)


@pytest.mark.asyncio
async def test_employee_allowed_tool_executes():
    result = await registry.execute("calculator", {"expression": "2 + 2"}, permissions={"run.execute"}, allowed_tools={"calculator"})
    assert result["result"] == 4


@pytest.mark.asyncio
async def test_employee_disallowed_tool_fails_closed():
    with pytest.raises(ValidationAppError, match="Tool is not allowed by Employee guardrails"):
        await registry.execute("current_time", {}, permissions={"run.execute"}, allowed_tools={"calculator"})


@pytest.mark.asyncio
async def test_employee_guardrail_applies_even_after_approval():
    from app.ai.tool_registry import RegisteredTool
    name = "_test_employee_guardrail_approval_tool"
    registry.register(RegisteredTool(
        name=name, description="test employee guardrail approval tool",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=lambda _: {"ok": True}, side_effects=False,
        required_permission="run.execute", requires_approval=True,
    ))
    try:
        with pytest.raises(ValidationAppError, match="Tool is not allowed by Employee guardrails"):
            await registry.execute(name, {}, permissions={"run.execute"}, approval_granted=True, allowed_tools={"calculator"})
    finally:
        registry._tools.pop(name, None)


@pytest.mark.asyncio
async def test_allowed_tools_none_preserves_legacy_behavior():
    result = await registry.execute("calculator", {"expression": "6 * 7"}, permissions={"run.execute"}, allowed_tools=None)
    assert result["result"] == 42


@pytest.mark.asyncio
async def test_employee_guardrail_does_not_replace_permission_guardrail():
    with pytest.raises(ValidationAppError, match="Missing permission for tool"):
        await registry.execute("calculator", {"expression": "2 + 2"}, permissions=set(), allowed_tools={"calculator"})


def test_workforce_market_risk_analysis_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_market_risk_analysis")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"


@pytest.mark.asyncio
async def test_workforce_market_risk_analysis_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_market_risk_analysis",
            {"symbols": ["AAPL"]},
            permissions={"run.execute"},
            allowed_tools={"workforce_market_risk_analysis"},
        )


def test_workforce_market_research_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_market_research")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"


def test_workforce_request_capacity_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_request_capacity")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"


@pytest.mark.asyncio
async def test_workforce_request_capacity_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_request_capacity",
            {},
            permissions={"run.execute"},
            allowed_tools={"workforce_request_capacity"},
        )


@pytest.mark.asyncio
async def test_workforce_request_capacity_dispatches_registered_handler(monkeypatch):
    from app.services import capacity_forecasting, license_service
    from app.services.capacity_forecasting import CapacityForecast
    from datetime import datetime, timezone
    from uuid import uuid4

    tenant_id = uuid4()
    forecast = CapacityForecast(
        tenant_id=tenant_id,
        window_days=14,
        horizon_days=7,
        sample_count=42,
        demand_samples_per_day=3.0,
        average_run_duration_seconds=120.0,
        current_ready_items=4,
        current_active_work_items=2,
        total_max_concurrency=8,
        total_available_slots=6,
        projected_arrivals=21.0,
        projected_required_concurrency=0.0041666667,
        projected_utilization=0.0005208333,
        projected_backlog=0.0,
        lower_bound_required_concurrency=0.0020833333,
        upper_bound_required_concurrency=0.00625,
        evidence_complete=True,
        rationale=["capacity evidence"],
        contract_version="stage9-capacity-forecast-v1",
        window_start=datetime(2026, 9, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )

    async def allow_entitlement(*args, **kwargs):
        return None

    async def capacity_forecast(db, *, tenant_id, window_days, horizon_days):
        assert db == "db-context"
        assert tenant_id == "tenant-context"
        assert window_days == 14
        assert horizon_days == 7
        return forecast

    monkeypatch.setattr(license_service, "assert_feature_entitlement", allow_entitlement)
    monkeypatch.setattr(capacity_forecasting, "capacity_forecast", capacity_forecast)

    result = await registry.execute(
        "workforce_request_capacity",
        {"window_days": 14, "horizon_days": 7},
        permissions={"run.execute"},
        allowed_tools={"workforce_request_capacity"},
        db="db-context",
        tenant_id="tenant-context",
    )
    assert result["window_days"] == 14
    assert result["horizon_days"] == 7
    assert result["sample_count"] == 42
    assert result["contract_version"] == "stage9-capacity-forecast-v1"
    assert result["tenant_id"] == str(tenant_id)


def test_workforce_prepare_ceo_report_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_prepare_ceo_report")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"


@pytest.mark.asyncio
async def test_workforce_prepare_ceo_report_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_prepare_ceo_report",
            {},
            permissions={"run.execute"},
            allowed_tools={"workforce_prepare_ceo_report"},
        )


@pytest.mark.asyncio
async def test_workforce_prepare_ceo_report_dispatches_registered_handler(monkeypatch):
    from app.services import agent_workforce_manager, license_service

    async def allow_entitlement(*args, **kwargs):
        return None

    async def dashboard(db, *, tenant_id, window_days):
        assert db == "db-context"
        assert tenant_id == "tenant-context"
        assert window_days == 7
        return {"work_items": {"status_counts": {"succeeded": 2}}}

    monkeypatch.setattr(license_service, "assert_feature_entitlement", allow_entitlement)
    monkeypatch.setattr(agent_workforce_manager, "get_workforce_dashboard", dashboard)

    result = await registry.execute(
        "workforce_prepare_ceo_report",
        {"window_days": 7},
        permissions={"run.execute"},
        allowed_tools={"workforce_prepare_ceo_report"},
        db="db-context",
        tenant_id="tenant-context",
    )
    assert result == {"work_items": {"status_counts": {"succeeded": 2}}}


def test_workforce_market_trading_plan_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_market_trading_plan")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"


@pytest.mark.asyncio
async def test_workforce_market_trading_plan_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_market_trading_plan",
            {"symbols": ["AAPL"]},
            permissions={"run.execute"},
            allowed_tools={"workforce_market_trading_plan"},
        )


@pytest.mark.asyncio
async def test_workforce_market_research_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_market_research",
            {"symbols": ["AAPL"]},
            permissions={"run.execute"},
            allowed_tools={"workforce_market_research"},
        )


@pytest.mark.asyncio
async def test_workforce_registered_handler_receives_runtime_context(monkeypatch):
    from dataclasses import replace
    from app.services import license_service

    name = "workforce_market_research"
    original = registry.get(name)
    calls = []

    async def handler(arguments, **context):
        calls.append((arguments, context))
        return {"ok": True}

    async def allow_entitlement(*args, **kwargs):
        return None

    monkeypatch.setattr(license_service, "assert_feature_entitlement", allow_entitlement)
    registry._tools[name] = replace(original, handler=handler)
    try:
        result = await registry.execute(
            name,
            {"symbols": ["AAPL"]},
            permissions={"run.execute"},
            allowed_tools={name},
            db="db-context",
            tenant_id="tenant-context",
        )
        assert result == {"ok": True}
        assert calls == [
            (
                {"symbols": ["AAPL"]},
                {"db": "db-context", "tenant_id": "tenant-context"},
            )
        ]
    finally:
        registry._tools[name] = original




def test_workforce_prepare_growth_report_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_prepare_growth_report")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"



@pytest.mark.asyncio
async def test_workforce_draft_campaign_plan_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_draft_campaign_plan",
            {"objective": "lead generation", "audience": "SMB", "channels": ["email"]},
            permissions={"run.execute"},
            allowed_tools={"workforce_draft_campaign_plan"},
        )


@pytest.mark.asyncio
async def test_workforce_draft_campaign_plan_dispatches_registered_handler(monkeypatch):
    from app.services import license_service

    async def allow_entitlement(*args, **kwargs):
        return None

    monkeypatch.setattr(license_service, "assert_feature_entitlement", allow_entitlement)

    result = await registry.execute(
        "workforce_draft_campaign_plan",
        {
            "objective": "lead generation",
            "audience": "SMB",
            "channels": ["Email", "social"],
            "duration_days": 21,
            "budget": 5000,
        },
        permissions={"run.execute"},
        allowed_tools={"workforce_draft_campaign_plan"},
        db="db-context",
        tenant_id="tenant-context",
    )
    assert result["status"] == "draft"
    assert result["channels"] == ["email", "social"]
    assert result["duration_days"] == 21
    assert result["governance"]["execution_required"] is True


def test_workforce_draft_campaign_plan_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_draft_campaign_plan")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"


@pytest.mark.asyncio
async def test_workforce_prepare_growth_report_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_prepare_growth_report",
            {},
            permissions={"run.execute"},
            allowed_tools={"workforce_prepare_growth_report"},
        )


@pytest.mark.asyncio
async def test_workforce_prepare_growth_report_dispatches_registered_handler(monkeypatch):
    from app.services import license_service, workforce_marketing_growth_report_service

    async def allow_entitlement(*args, **kwargs):
        return None

    async def growth_report(db, *, tenant_id, window_days):
        assert db == "db-context"
        assert tenant_id == "tenant-context"
        assert window_days == 14
        return {"orders": {"count": 3}, "sales_pipeline": {"weighted_pipeline": 1200.0}}

    monkeypatch.setattr(license_service, "assert_feature_entitlement", allow_entitlement)
    monkeypatch.setattr(
        workforce_marketing_growth_report_service,
        "prepare_growth_report",
        growth_report,
    )

    result = await registry.execute(
        "workforce_prepare_growth_report",
        {"window_days": 14},
        permissions={"run.execute"},
        allowed_tools={"workforce_prepare_growth_report"},
        db="db-context",
        tenant_id="tenant-context",
    )
    assert result == {"orders": {"count": 3}, "sales_pipeline": {"weighted_pipeline": 1200.0}}



@pytest.mark.asyncio
async def test_workforce_coordinate_content_requires_tenant_context():
    with pytest.raises(ValidationAppError, match="active tenant Run context"):
        await registry.execute(
            "workforce_coordinate_content",
            {
                "objective": "launch",
                "channels": ["social"],
                "audience": "SMB",
                "key_message": "Save time",
            },
            permissions={"run.execute"},
            allowed_tools={"workforce_coordinate_content"},
        )


@pytest.mark.asyncio
async def test_workforce_coordinate_content_dispatches_registered_handler(monkeypatch):
    from app.services import license_service

    async def allow_entitlement(*args, **kwargs):
        return None

    monkeypatch.setattr(license_service, "assert_feature_entitlement", allow_entitlement)

    result = await registry.execute(
        "workforce_coordinate_content",
        {
            "objective": "launch",
            "channels": ["Social", "email"],
            "audience": "SMB",
            "key_message": "Save time",
            "offer": "Free trial",
        },
        permissions={"run.execute"},
        allowed_tools={"workforce_coordinate_content"},
        db="db-context",
        tenant_id="tenant-context",
    )
    assert result["status"] == "planned"
    assert [item["channel"] for item in result["deliverables"]] == ["social", "email"]
    assert result["governance"]["publication_requires_separate_execution"] is True


def test_workforce_coordinate_content_is_read_only_and_non_approval_gated():
    tool = registry.get("workforce_coordinate_content")
    assert tool.side_effects is False
    assert tool.requires_approval is False
    assert tool.required_permission == "run.execute"

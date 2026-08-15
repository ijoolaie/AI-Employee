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
        "calculator",
        "current_time",
        "send_email",
        "analyze_dataset",
        "analyze_document",
        "create_invoice",
        "update_invoice_status",
        "analyze_invoice_file",
        "export_invoice_pdf",
        "invoice_financial_summary",
        "create_order",
        "update_order_status",
        "analyze_order_file",
        "order_summary",
        "link_order_invoice",
        "create_deal",
        "update_deal_stage",
        "sales_pipeline_summary",
        "sales_forecast",
        "search_products",
        "get_product",
        "check_inventory",
        "get_order",
        "track_order",
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
        prompt_template="You are a calculator employee.",
        prompt_version="1",
        context=ExecutionContext(input_data={}),
        allowed_tools=["calculator"],
    )
    assert [tool.name for tool in assembly.tools] == ["calculator"]
    assert assembly.metadata["tool_count"] == 1


def test_unknown_allowed_tool_fails_closed():
    with pytest.raises(ValidationAppError):
        assemble_employee_prompt(
            prompt_template="test",
            prompt_version="1",
            context=ExecutionContext(input_data={}),
            allowed_tools=["not_registered"],
        )


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
    registry.register(
        RegisteredTool(
            name=name,
            description="test gated tool",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            handler=lambda _: {"ok": True},
            side_effects=True,
            required_permission="run.execute",
            requires_approval=True,
        )
    )
    with pytest.raises(ValidationAppError):
        await registry.execute(name, {}, permissions={"run.execute"}, approval_granted=False)
    result = await registry.execute(name, {}, permissions={"run.execute"}, approval_granted=True)
    assert result == {"ok": True}
    registry._tools.pop(name, None)

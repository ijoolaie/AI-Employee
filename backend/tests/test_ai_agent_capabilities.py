"""Acceptance contracts for Agent Tool Calling, structured arguments and multi-step execution."""

import json

import pytest

from app.ai.prompt_assembly import ExecutionContext, assemble_employee_prompt
from app.ai.schemas import ChatMessage, ChatRequest, ChatResult, ToolCall
from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError


def test_tool_call_contract_exposes_json_schema_to_provider():
    assembly = assemble_employee_prompt(
        prompt_template="Use the calculator when arithmetic is required.",
        prompt_version="1",
        context=ExecutionContext(input_data={"request": "2 + 2"}),
        allowed_tools=["calculator"],
    )
    assert len(assembly.tools) == 1
    assert assembly.tools[0].name == "calculator"
    assert assembly.tools[0].input_schema["type"] == "object"
    assert "expression" in assembly.tools[0].input_schema["properties"]


@pytest.mark.asyncio
async def test_structured_arguments_are_validated_before_tool_side_effects():
    with pytest.raises(ValidationAppError, match="Invalid arguments"):
        await registry.execute("calculator", {}, permissions={"run.execute"})
    with pytest.raises(ValidationAppError, match="Invalid arguments"):
        await registry.execute(
            "calculator",
            {"expression": "2 + 2", "unexpected": "blocked"},
            permissions={"run.execute"},
        )
    result = await registry.execute(
        "calculator", {"expression": "2 + 2"}, permissions={"run.execute"}
    )
    assert result["result"] == 4


def test_provider_tool_call_shape_is_modelled_as_structured_arguments():
    call = ToolCall(id="call-1", name="calculator", arguments={"expression": "3 * 7"})
    result = ChatResult(
        content="",
        prompt_tokens=1,
        completion_tokens=1,
        tool_calls=[call],
    )
    assert result.tool_calls[0].arguments == {"expression": "3 * 7"}
    assert isinstance(result.tool_calls[0].arguments, dict)


def test_multi_step_execution_contract_is_bounded():
    from app.agents.planner import autonomy_settings, parse_plan

    config = autonomy_settings({"autonomy": {"enabled": True, "max_steps": 3}})
    assert config["enabled"] is True
    assert config["max_steps"] == 3
    payload = {
        "goal": "complete a multi-step task",
        "steps": [
            {"id": "step-1", "objective": "inspect", "suggested_tools": ["calculator"]},
            {"id": "step-2", "objective": "calculate", "suggested_tools": ["calculator"]},
            {"id": "step-3", "objective": "finish", "suggested_tools": []},
        ],
    }
    plan = parse_plan(json.dumps(payload), allowed_tools=["calculator"], max_steps=3)
    assert len(plan.steps) == 3
    overflow = {**payload, "steps": payload["steps"] + [{"objective": "overflow", "suggested_tools": []}]}
    with pytest.raises(ValidationAppError):
        parse_plan(json.dumps(overflow), allowed_tools=["calculator"], max_steps=3)


def test_chat_request_carries_tool_definitions_across_turns():
    assembly = assemble_employee_prompt(
        prompt_template="calculator",
        prompt_version="1",
        context=ExecutionContext(input_data={}),
        allowed_tools=["calculator"],
    )
    request = ChatRequest(
        messages=[ChatMessage(role="user", content="calculate 5 + 5")],
        model="agent-test",
        tools=assembly.tools,
    )
    assert request.tools[0].name == "calculator"
    assert request.tools[0].input_schema["type"] == "object"

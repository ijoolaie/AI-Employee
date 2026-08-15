import json
import pytest

from app.agents.planner import autonomy_settings, parse_plan
from app.core.exceptions import ValidationAppError


def test_autonomy_is_opt_in():
    assert autonomy_settings({})["enabled"] is False
    cfg = autonomy_settings({"autonomy": {"enabled": True, "max_steps": 4}})
    assert cfg == {"enabled": True, "max_steps": 4, "require_plan": True}


def test_parse_plan_accepts_json_fence_and_rejects_unknown_tools():
    payload = {
        "goal": "Prepare a sales summary",
        "steps": [
            {"id": "step-1", "objective": "Summarize the pipeline", "suggested_tools": ["sales_pipeline_summary"]}
        ],
    }
    plan = parse_plan("```json\n" + json.dumps(payload) + "\n```", allowed_tools=["sales_pipeline_summary"], max_steps=3)
    assert plan.goal == "Prepare a sales summary"
    assert plan.steps[0].suggested_tools == ["sales_pipeline_summary"]

    with pytest.raises(ValidationAppError):
        parse_plan(json.dumps({**payload, "steps": [{**payload["steps"][0], "suggested_tools": ["secret_tool"]}]}), allowed_tools=["calculator"], max_steps=3)


def test_parse_plan_enforces_step_limit():
    payload = {"goal": "x", "steps": [{"objective": str(i), "suggested_tools": []} for i in range(4)]}
    with pytest.raises(ValidationAppError):
        parse_plan(json.dumps(payload), allowed_tools=[], max_steps=3)


def test_autonomous_plan_is_assembled_as_guidance():
    from app.ai.prompt_assembly import ExecutionContext, assemble_employee_prompt

    assembly = assemble_employee_prompt(
        prompt_template="Complete the user's request.",
        prompt_version="1",
        context=ExecutionContext(
            input_data={"message": "summarize sales"},
            autonomous_plan={
                "version": "1",
                "goal": "Summarize sales",
                "steps": [{"id": "step-1", "objective": "Read pipeline", "suggested_tools": ["sales_pipeline_summary"]}],
            },
        ),
        allowed_tools=["sales_pipeline_summary"],
    )
    assert "## Autonomous Execution Plan" in assembly.messages[0].content
    assert assembly.metadata["context_sections"][-1] == "autonomous_plan"

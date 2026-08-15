"""Provider-agnostic autonomous planning for Employee Runs.

The planner is deliberately opt-in. It produces a small, validated task plan
that is fed back into the normal Run tool loop; it never executes tools itself.
That keeps permissions, approvals, auditing, and tenant boundaries in the
existing ToolRegistry execution boundary.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.ai.schemas import ChatMessage, ChatRequest, ToolDefinition
from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError

PLAN_VERSION = "1"


@dataclass(frozen=True)
class PlanStep:
    id: str
    objective: str
    suggested_tools: list[str]


@dataclass(frozen=True)
class ExecutionPlan:
    goal: str
    steps: list[PlanStep]
    version: str = PLAN_VERSION

    def as_context(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "goal": self.goal,
            "steps": [
                {
                    "id": step.id,
                    "objective": step.objective,
                    "suggested_tools": step.suggested_tools,
                }
                for step in self.steps
            ],
        }


def autonomy_settings(rules: dict[str, Any]) -> dict[str, Any]:
    raw = rules.get("autonomy", {}) if isinstance(rules, dict) else {}
    if not isinstance(raw, dict):
        raise ValidationAppError("Employee autonomy configuration must be an object")
    enabled = bool(raw.get("enabled", False))
    max_steps = int(raw.get("max_steps", 6))
    if max_steps < 1 or max_steps > 12:
        raise ValidationAppError("autonomy.max_steps must be between 1 and 12")
    return {
        "enabled": enabled,
        "max_steps": max_steps,
        "require_plan": bool(raw.get("require_plan", True)),
    }


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Be tolerant of a short natural-language prefix from local models.
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValidationAppError("Autonomous planner returned invalid JSON") from exc
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as inner:
            raise ValidationAppError("Autonomous planner returned invalid JSON") from inner
    if not isinstance(payload, dict):
        raise ValidationAppError("Autonomous planner response must be a JSON object")
    return payload


def parse_plan(text: str, *, allowed_tools: list[str], max_steps: int) -> ExecutionPlan:
    payload = _extract_json(text)
    goal = str(payload.get("goal", "")).strip()
    raw_steps = payload.get("steps")
    if not goal or not isinstance(raw_steps, list):
        raise ValidationAppError("Autonomous planner must return goal and steps")
    if not raw_steps or len(raw_steps) > max_steps:
        raise ValidationAppError(
            "Autonomous planner returned an invalid number of steps",
            details={"max_steps": max_steps},
        )

    allowed = set(allowed_tools)
    steps: list[PlanStep] = []
    for index, raw in enumerate(raw_steps, start=1):
        if not isinstance(raw, dict):
            raise ValidationAppError("Autonomous planner step must be an object")
        objective = str(raw.get("objective", "")).strip()
        if not objective:
            raise ValidationAppError("Autonomous planner step has no objective")
        suggestions = raw.get("suggested_tools", [])
        if not isinstance(suggestions, list):
            raise ValidationAppError("Autonomous planner suggested_tools must be a list")
        suggested_tools = [str(name) for name in suggestions]
        unknown = [name for name in suggested_tools if name not in allowed]
        if unknown:
            raise ValidationAppError(
                "Autonomous planner suggested an unavailable tool",
                details={"tools": unknown},
            )
        steps.append(
            PlanStep(
                id=str(raw.get("id") or f"step-{index}"),
                objective=objective,
                suggested_tools=suggested_tools,
            )
        )
    return ExecutionPlan(goal=goal, steps=steps)


async def create_plan(
    gateway,
    db,
    *,
    tenant_id,
    run_id,
    model: str,
    input_data: dict[str, Any],
    prompt_template: str,
    allowed_tools: list[str],
    max_steps: int,
) -> ExecutionPlan:
    definitions: list[ToolDefinition] = registry.definitions_for(allowed_tools)
    tool_catalog = [
        {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
        for tool in definitions
    ]
    system = (
        "You are the planning component of an AI Employee. "
        "Create a minimal executable plan for the user's goal. "
        "Do not invent tools. Do not execute anything. "
        "Return ONLY JSON with this shape: "
        '{"goal":"...","steps":[{"id":"step-1","objective":"...","suggested_tools":["tool_name"]}]}. '
        f"Use at most {max_steps} steps."
    )
    user = json.dumps(
        {
            "employee_instruction": prompt_template,
            "input": input_data,
            "available_tools": tool_catalog,
        },
        ensure_ascii=False,
        default=str,
    )
    result = await gateway.chat(
        db,
        ChatRequest(
            messages=[ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
            model=model,
            max_tokens=900,
            temperature=0.1,
        ),
        tenant_id=tenant_id,
        run_id=run_id,
        prompt_version="autonomy-planner-v1",
        call_metadata={"purpose": "autonomous_planning", "max_steps": max_steps},
    )
    return parse_plan(result.content, allowed_tools=allowed_tools, max_steps=max_steps)

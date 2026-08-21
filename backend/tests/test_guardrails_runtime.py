import pytest

from app.ai.tool_registry import RegisteredTool, registry
from app.core.exceptions import ValidationAppError


@pytest.mark.asyncio
async def test_tool_registry_enforces_employee_allowed_tools():
    name = "_test_guardrail_tool"
    registry.register(
        RegisteredTool(
            name=name,
            description="test guardrail tool",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            handler=lambda _: {"ok": True},
            required_permission="run.execute",
        )
    )
    try:
        with pytest.raises(ValidationAppError, match="not allowed by Employee guardrails"):
            await registry.execute(
                name,
                {},
                permissions={"run.execute"},
                allowed_tools={"calculator"},
            )

        result = await registry.execute(
            name,
            {},
            permissions={"run.execute"},
            allowed_tools={name},
        )
        assert result == {"ok": True}
    finally:
        registry._tools.pop(name, None)


@pytest.mark.asyncio
async def test_employee_guardrail_does_not_bypass_tool_permission():
    name = "_test_guardrail_permission_tool"
    registry.register(
        RegisteredTool(
            name=name,
            description="test guardrail permission tool",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            handler=lambda _: {"ok": True},
            required_permission="run.execute",
        )
    )
    try:
        with pytest.raises(ValidationAppError, match="Missing permission"):
            await registry.execute(
                name,
                {},
                permissions=set(),
                allowed_tools={name},
            )
    finally:
        registry._tools.pop(name, None)

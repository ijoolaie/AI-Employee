import pytest

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError
from app.services.tool_approval_policy import MANDATORY_APPROVAL_TOOLS, requires_approval

from app.services.tool_approval_policy_bootstrap import install as install_tool_approval_policy

install_tool_approval_policy()


def test_mandatory_side_effect_tools_are_approval_gated():
    expected = {
        "create_order",
        "create_invoice",
        "update_order_status",
        "update_invoice_status",
        "create_deal",
        "update_deal_stage",
        "link_order_invoice",
        "send_email",
        "whatsapp.send_text",
    }
    assert MANDATORY_APPROVAL_TOOLS == expected
    for name in expected:
        assert requires_approval(name) is True
        assert registry.get(name).side_effects is True
        assert registry.get(name).external_side_effects is True
        assert registry.get(name).requires_approval is True


def test_whatsapp_outbound_tool_schema_is_restricted_and_registered():
    tool = registry.get("whatsapp.send_text")
    assert set(tool.input_schema["required"]) == {"channel_id", "recipient", "text"}
    assert tool.input_schema["additionalProperties"] is False
    assert tool.input_schema["properties"]["text"]["maxLength"] == 4096
    assert tool.required_permission == "run.execute"


def test_policy_cannot_be_disabled_by_local_tool_flag():
    assert requires_approval("create_order", explicitly_required=False) is True
    assert requires_approval("whatsapp.send_text", explicitly_required=False) is True
    assert requires_approval("calculator", explicitly_required=False) is False
    assert requires_approval("calculator", explicitly_required=True) is True


@pytest.mark.asyncio
async def test_whatsapp_send_is_blocked_without_durable_approval_before_db_or_provider():
    with pytest.raises(ValidationAppError, match="Human approval required for tool: whatsapp.send_text"):
        await registry.execute(
            "whatsapp.send_text",
            {"channel_id": "12345678-1234-1234-1234-123456789012", "recipient": "+15551234567", "text": "hello"},
            permissions={"run.execute"},
            approval_granted=False,
            allowed_tools={"whatsapp.send_text"},
        )


@pytest.mark.asyncio
async def test_mandatory_tool_is_blocked_without_approval():
    with pytest.raises(ValidationAppError, match="Human approval required for tool: create_order"):
        await registry.execute(
            "create_order",
            {"customer_name": "Test", "line_items": [{"description": "item", "unit_price": 1}]},
            permissions={"run.execute"},
            approval_granted=False,
            allowed_tools={"create_order"},
        )

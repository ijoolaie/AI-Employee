import pytest

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError
from app.services.tool_approval_policy import MANDATORY_APPROVAL_TOOLS, requires_approval

# Import the bootstrap explicitly in this focused unit test so the assertion
# exercises the same policy activation used by the Run service package import.
import app.services.tool_approval_policy_bootstrap  # noqa: F401,E402


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
    }
    assert MANDATORY_APPROVAL_TOOLS == expected
    for name in expected:
        assert requires_approval(name) is True
        assert registry.get(name).side_effects is True
        assert registry.get(name).requires_approval is True


def test_policy_cannot_be_disabled_by_local_tool_flag():
    assert requires_approval("create_order", explicitly_required=False) is True
    assert requires_approval("calculator", explicitly_required=False) is False
    assert requires_approval("calculator", explicitly_required=True) is True


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

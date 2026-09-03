from app.ai.tool_registry import registry
from app.services.sales_readiness_service import TEMPLATES, _validate_template_tools


def test_all_built_in_template_tools_are_registered():
    registered = {tool.name for tool in registry.list()}
    for template in TEMPLATES:
        assert set(template["allowed_tools"]).issubset(registered), template["code"]
        _validate_template_tools(template)


def test_sales_template_requires_approval_for_order_creation():
    sales = next(template for template in TEMPLATES if template["code"] == "sales_assistant")
    assert "create_order" in sales["allowed_tools"]
    assert "create_order" in sales["rules"]["require_approval_for"]
    assert registry.get("create_order").requires_approval is True

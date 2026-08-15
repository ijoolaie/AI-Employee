from app.ai.tool_registry import registry


def test_sales_readiness_product_tools_registered():
    names = {tool.name for tool in registry.list()}
    assert {"search_products", "get_product", "check_inventory"}.issubset(names)


def test_sales_readiness_tool_definitions_are_safe_read_only():
    tools = {tool.name: tool for tool in registry.list()}
    for name in ("search_products", "get_product", "check_inventory"):
        assert tools[name].side_effects is False
        assert tools[name].required_permission == "run.execute"

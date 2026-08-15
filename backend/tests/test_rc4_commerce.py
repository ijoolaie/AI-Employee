from app.ai.tool_registry import registry
from app.services.commerce_integration_service import public_config


def test_rc4_commerce_tools_registered():
    names = {tool.name for tool in registry.list()}
    assert {"search_products", "get_product", "check_inventory", "create_order", "get_order", "track_order"}.issubset(names)


def test_rc4_read_only_order_tools_are_not_side_effecting():
    tools = {tool.name: tool for tool in registry.list()}
    assert tools["get_order"].side_effects is False
    assert tools["track_order"].side_effects is False


def test_rc4_integration_public_config_redacts_access_token():
    from types import SimpleNamespace
    public = public_config(SimpleNamespace(config={"shop_domain": "demo.myshopify.com", "access_token": "secret-token", "api_version": "2025-10"}))
    assert public["config"]["access_token"] == "••••••••"
    assert public["config"]["shop_domain"] == "demo.myshopify.com"

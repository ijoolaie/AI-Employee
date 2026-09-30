from app.ai.tool_registry import registry
from app.services.ai_workforce_roles import WORKFORCE_ROLES
from scripts.workforce_binding_inventory import build_inventory


def test_w0_inventory_is_code_derived_and_all_bound_tools_are_registered():
    inventory = build_inventory()
    registered = {tool.name for tool in registry.list()}
    assert inventory["role_count"] == len(WORKFORCE_ROLES)
    assert inventory["registered_tool_count"] == len(registered)
    assert inventory["explicit_binding_count"] == sum(
        bool(contract.tool_names)
        for role in WORKFORCE_ROLES
        for contract in role.capability_contract
    )
    for role in WORKFORCE_ROLES:
        for contract in role.capability_contract:
            for tool_name in contract.tool_names:
                assert tool_name in registered, (role.code, contract.operation, tool_name)


def test_w0_approval_required_operations_have_no_routine_tool_binding():
    for role in WORKFORCE_ROLES:
        for contract in role.capability_contract:
            if contract.operation in role.approval_required_operations:
                assert contract.approval_required is True

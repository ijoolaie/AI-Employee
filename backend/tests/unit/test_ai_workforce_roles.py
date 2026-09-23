from __future__ import annotations

import pytest

from app.core.exceptions import ValidationAppError

from app.services.ai_workforce_roles import (
    get_workforce_role,
    get_workforce_role_template,
    workforce_capability_contract_snapshot,
    workforce_template_capability_contract,
    is_operation_allowed,
    list_workforce_role_templates,
    list_workforce_roles,
)


def test_catalog_contains_internal_manager_and_requested_next_roles() -> None:
    codes = {item["code"] for item in list_workforce_roles()}
    assert codes == {
        "ai_internal_manager",
        "ai_marketing_advertising_manager",
        "ai_graphic_designer",
        "ai_software_developer",
        "ai_trader",
    }


def test_internal_manager_requires_explicit_ceo_delegation_for_routine_operations() -> None:
    assert not is_operation_allowed("ai_internal_manager", "assign_task")
    assert is_operation_allowed("ai_internal_manager", "assign_task", manager_delegated=True)


@pytest.mark.parametrize(
    ("role", "operation"),
    [
        ("ai_internal_manager", "hire_or_provision_employee"),
        ("ai_internal_manager", "financial_commitment"),
        ("ai_marketing_advertising_manager", "paid_campaign_launch"),
        ("ai_graphic_designer", "commercial_license_purchase"),
        ("ai_software_developer", "production_critical_change"),
        ("ai_software_developer", "security_sensitive_change"),
        ("ai_trader", "capital_allocation"),
        ("ai_trader", "order_execution"),
        ("ai_trader", "withdrawal"),
    ],
)
def test_high_impact_operations_remain_human_approval_gated(role: str, operation: str) -> None:
    assert not is_operation_allowed(role, operation, manager_delegated=True)


def test_trader_research_can_be_prepared_but_execution_is_not_autonomous() -> None:
    assert is_operation_allowed("ai_trader", "market_research")
    assert is_operation_allowed("ai_trader", "prepare_trading_plan")
    assert is_operation_allowed("ai_trader", "stage_order_for_review")
    assert not is_operation_allowed("ai_trader", "order_execution")


def test_unknown_role_fails_closed() -> None:
    with pytest.raises(KeyError):
        get_workforce_role("does_not_exist")


def test_four_requested_roles_have_first_party_workforce_templates() -> None:
    templates = list_workforce_role_templates()
    assert {item["role_code"] for item in templates} == {
        "ai_marketing_advertising_manager",
        "ai_graphic_designer",
        "ai_software_developer",
        "ai_trader",
    }
    assert len(templates) == 4
    for template in templates:
        assert template["slug"]
        assert template["name"]
        assert template["name_fa"]
        assert template["description"]
        assert template["description_fa"]
        assert get_workforce_role_template(template["role_code"]).slug == template["slug"]



def test_every_workforce_operation_has_an_explicit_capability_contract() -> None:
    from app.services.ai_workforce_roles import get_workforce_capability_contract, list_workforce_roles

    for role in list_workforce_roles():
        operations = set(role["allowed_routine_operations"]) | set(role["approval_required_operations"])
        contracts = {item["operation"]: item for item in role["capability_contract"]}
        assert set(contracts) == operations
        for operation in operations:
            contract = get_workforce_capability_contract(role["code"], operation)
            assert contract.capability_code == f"workforce.{operation}"
            assert contract.required_permissions
            assert contract.approval_required is (operation in role["approval_required_operations"])


def test_unbound_workforce_operation_fails_closed_before_tool_execution() -> None:
    from app.services.ai_workforce_roles import assert_workforce_tool_binding

    with pytest.raises(ValidationAppError, match="no approved Tool Registry binding"):
        assert_workforce_tool_binding("ai_trader", "market_research", "calculator")


def test_workforce_capability_contract_snapshot_is_json_safe_and_role_scoped() -> None:
    snapshot = workforce_capability_contract_snapshot("ai_trader")
    assert snapshot
    assert all(set(item) == {"operation", "capability_code", "tool_names", "required_permissions", "approval_required"} for item in snapshot)
    assert any(item["operation"] == "market_research" for item in snapshot)
    assert not any(item["operation"] == "draft_campaign_plan" for item in snapshot)


def test_workforce_template_capability_contract_binds_catalog_role_exactly() -> None:
    binding = workforce_template_capability_contract("ai_trader")
    assert binding["workforce_role_code"] == "ai_trader"
    assert binding["workforce_capability_contract"] == workforce_capability_contract_snapshot("ai_trader")

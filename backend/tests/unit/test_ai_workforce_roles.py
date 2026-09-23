from __future__ import annotations

import pytest

from app.services.ai_workforce_roles import (
    get_workforce_role,
    is_operation_allowed,
    list_workforce_roles,
    validate_manager_proposable_role,
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

@pytest.mark.parametrize(
    "role_code",
    [
        "ai_marketing_advertising_manager",
        "ai_graphic_designer",
        "ai_software_developer",
        "ai_trader",
    ],
)
def test_next_roles_are_explicit_manager_proposal_targets(role_code: str) -> None:
    assert validate_manager_proposable_role(role_code).code == role_code


def test_internal_manager_is_not_a_next_role_proposal_target() -> None:
    with pytest.raises(ValueError, match="not eligible"):
        validate_manager_proposable_role("ai_internal_manager")

"""First-party AI Company workforce role catalog and approval boundaries.

This module is intentionally declarative. It does not provision AgentDefinitions,
AgentTemplates, or AgentInstances. Provisioning remains governed by the existing
template evaluation, Board/CEO approval, access-review, and activation flows.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

ApprovalClass = Literal["routine_delegable", "human_approval_required"]


@dataclass(frozen=True)
class WorkforceRole:
    code: str
    name: str
    name_fa: str
    category: str
    supervisor: str
    purpose: str
    approval_class: ApprovalClass
    allowed_routine_operations: tuple[str, ...]
    approval_required_operations: tuple[str, ...]


WORKFORCE_ROLES: tuple[WorkforceRole, ...] = (
    WorkforceRole(
        code="ai_internal_manager",
        name="AI Internal Manager",
        name_fa="مدیر داخلی هوش مصنوعی",
        category="executive_governance",
        supervisor="human_ceo",
        purpose="Coordinate the specialized AI workforce, monitor workload/KPI/SLA, and prepare governed workforce decisions.",
        approval_class="routine_delegable",
        allowed_routine_operations=("assign_task", "reprioritize_task", "coordinate_handoff", "balance_workload", "request_workforce_capacity", "prepare_ceo_report", "prepare_budget_estimate", "prepare_cost_optimization"),
        approval_required_operations=("hire_or_provision_employee", "retire_employee", "transfer_employee", "replace_employee", "financial_commitment", "material_resource_commitment", "security_sensitive_change", "legal_commitment", "production_critical_change", "irreversible_action"),
    ),
    WorkforceRole(
        code="ai_marketing_advertising_manager",
        name="AI Marketing & Advertising Manager",
        name_fa="مدیر بازاریابی و تبلیغات هوش مصنوعی",
        category="marketing_growth",
        supervisor="ai_internal_manager",
        purpose="Plan campaigns, coordinate marketing work, and analyze campaign performance.",
        approval_class="routine_delegable",
        allowed_routine_operations=("draft_campaign_plan", "coordinate_content", "analyze_campaign_performance", "prepare_growth_report"),
        approval_required_operations=("paid_campaign_launch", "material_ad_spend", "contractual_commitment", "external_purchase"),
    ),
    WorkforceRole(
        code="ai_graphic_designer",
        name="AI Graphic Designer",
        name_fa="طراح گرافیک هوش مصنوعی",
        category="marketing_creative",
        supervisor="ai_internal_manager",
        purpose="Produce brand, advertising, presentation, and social visual assets.",
        approval_class="routine_delegable",
        allowed_routine_operations=("create_visual_asset", "revise_visual_asset", "prepare_brand_variant", "prepare_campaign_creative"),
        approval_required_operations=("paid_asset_procurement", "commercial_license_purchase", "material_external_spend", "contractual_commitment"),
    ),
    WorkforceRole(
        code="ai_software_developer",
        name="AI Software Developer",
        name_fa="توسعه‌دهنده نرم‌افزار هوش مصنوعی",
        category="technology_engineering",
        supervisor="ai_internal_manager",
        purpose="Implement product changes, fixes, integrations, tests, and routine engineering work.",
        approval_class="routine_delegable",
        allowed_routine_operations=("implement_routine_fix", "write_tests", "prepare_integration", "refactor_non_critical_code", "prepare_change_proposal"),
        approval_required_operations=("production_critical_change", "security_sensitive_change", "privileged_access_change", "material_resource_consumption", "irreversible_data_change"),
    ),
    WorkforceRole(
        code="ai_trader",
        name="AI Trader",
        name_fa="معامله‌گر هوش مصنوعی",
        category="finance",
        supervisor="ai_internal_manager",
        purpose="Perform market research, risk analysis, trading-plan preparation, and order staging within explicit limits.",
        approval_class="human_approval_required",
        allowed_routine_operations=("market_research", "risk_analysis", "prepare_trading_plan", "stage_order_for_review"),
        approval_required_operations=("capital_allocation", "order_execution", "leverage_change", "withdrawal", "material_financial_commitment"),
    ),
)


MANAGER_PROPOSABLE_ROLE_CODES = frozenset({
    "ai_marketing_advertising_manager",
    "ai_graphic_designer",
    "ai_software_developer",
    "ai_trader",
})


def validate_manager_proposable_role(role_code: str) -> WorkforceRole:
    """Return a role only when it is an approved next-role Manager proposal target."""
    if role_code not in MANAGER_PROPOSABLE_ROLE_CODES:
        raise ValueError(f"Role is not eligible for Internal Manager proposal: {role_code}")
    return get_workforce_role(role_code)


def list_workforce_roles() -> list[dict]:
    return [asdict(role) for role in WORKFORCE_ROLES]


def get_workforce_role(code: str) -> WorkforceRole:
    for role in WORKFORCE_ROLES:
        if role.code == code:
            return role
    raise KeyError(f"Unknown AI workforce role: {code}")


def is_operation_allowed(role_code: str, operation: str, *, manager_delegated: bool = False) -> bool:
    role = get_workforce_role(role_code)
    if operation in role.approval_required_operations:
        return False
    if operation not in role.allowed_routine_operations:
        return False
    if role.code == "ai_internal_manager":
        return manager_delegated
    return True

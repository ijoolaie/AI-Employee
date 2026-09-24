"""First-party AI Company workforce role catalog and approval boundaries.

This module is intentionally declarative. It does not provision AgentDefinitions,
AgentTemplates, or AgentInstances. Provisioning remains governed by the existing
template evaluation, Board/CEO approval, access-review, and activation flows.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from app.core.exceptions import ValidationAppError

ApprovalClass = Literal["routine_delegable", "human_approval_required"]


@dataclass(frozen=True)
class WorkforceCapabilityContract:
    """Machine-readable binding between an operation and execution authority."""

    operation: str
    capability_code: str
    tool_names: tuple[str, ...]
    required_permissions: tuple[str, ...]
    approval_required: bool


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
    capability_contract: tuple[WorkforceCapabilityContract, ...]


@dataclass(frozen=True)
class WorkforceRoleTemplate:
    slug: str
    role_code: str
    name: str
    name_fa: str
    description: str
    description_fa: str



def _contracts(
    routine: tuple[str, ...] | list[str],
    approval_required: tuple[str, ...] | list[str],
    tool_bindings: dict[str, tuple[str, ...]] | None = None,
) -> tuple[WorkforceCapabilityContract, ...]:
    return tuple(
        WorkforceCapabilityContract(
            operation=operation,
            capability_code=f"workforce.{operation}",
            tool_names=(tool_bindings or {}).get(operation, ()),
            required_permissions=("run.execute",),
            approval_required=operation in approval_required,
        )
        for operation in (*routine, *approval_required)
    )

WORKFORCE_ROLES: tuple[WorkforceRole, ...] = (
    WorkforceRole(
        code="ai_internal_manager",
        name="AI Internal Manager",
        name_fa="مدیر داخلی هوش مصنوعی",
        category="executive_governance",
        supervisor="human_ceo",
        purpose="Coordinate the specialized AI workforce, monitor workload/KPI/SLA, and prepare governed workforce decisions.",
        approval_class="routine_delegable",
        allowed_routine_operations=(
            "assign_task",
            "reprioritize_task",
            "coordinate_handoff",
            "balance_workload",
            "request_workforce_capacity",
            "prepare_ceo_report",
            "prepare_budget_estimate",
            "prepare_cost_optimization",
        ),
        approval_required_operations=(
            "hire_or_provision_employee", "retire_employee", "transfer_employee", "replace_employee",
            "financial_commitment", "material_resource_commitment", "security_sensitive_change",
            "legal_commitment", "production_critical_change", "irreversible_action",
        ),
        capability_contract=_contracts(
            ("assign_task", "reprioritize_task", "coordinate_handoff", "balance_workload", "request_workforce_capacity", "prepare_ceo_report", "prepare_budget_estimate", "prepare_cost_optimization"),
            ("hire_or_provision_employee", "retire_employee", "transfer_employee", "replace_employee", "financial_commitment", "material_resource_commitment", "security_sensitive_change", "legal_commitment", "production_critical_change", "irreversible_action"),
        ),
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
        capability_contract=_contracts(["draft_campaign_plan","coordinate_content","analyze_campaign_performance","prepare_growth_report"], ["paid_campaign_launch","material_ad_spend","contractual_commitment","external_purchase"]),
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
        capability_contract=_contracts(["create_visual_asset","revise_visual_asset","prepare_brand_variant","prepare_campaign_creative"], ["paid_asset_procurement","commercial_license_purchase","material_external_spend","contractual_commitment"]),
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
        capability_contract=_contracts(["implement_routine_fix","write_tests","prepare_integration","refactor_non_critical_code","prepare_change_proposal"], ["production_critical_change","security_sensitive_change","privileged_access_change","material_resource_consumption","irreversible_data_change"]),
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
        capability_contract=_contracts(
            ["market_research","risk_analysis","prepare_trading_plan","stage_order_for_review"],
            ["capital_allocation","order_execution","leverage_change","withdrawal","material_financial_commitment"],
            {"market_research": ("workforce_market_research",), "risk_analysis": ("workforce_market_risk_analysis",)},
        ),
    ),
)


# These are first-party role templates for the Internal Manager workforce catalog.
# They are not active AgentTemplates/AgentInstances; provisioning remains governed.
WORKFORCE_ROLE_TEMPLATES: tuple[WorkforceRoleTemplate, ...] = (
    WorkforceRoleTemplate(
        slug="ai-marketing-advertising-manager",
        role_code="ai_marketing_advertising_manager",
        name="AI Marketing & Advertising Manager",
        name_fa="مدیر بازاریابی و تبلیغات هوش مصنوعی",
        description="Plans campaigns, coordinates marketing work, and analyzes campaign performance.",
        description_fa="کمپین‌ها را برنامه‌ریزی می‌کند، فعالیت‌های بازاریابی را هماهنگ می‌کند و عملکرد کمپین را تحلیل می‌کند.",
    ),
    WorkforceRoleTemplate(
        slug="ai-graphic-designer",
        role_code="ai_graphic_designer",
        name="AI Graphic Designer",
        name_fa="طراح گرافیک هوش مصنوعی",
        description="Produces brand, advertising, presentation, and social visual assets.",
        description_fa="دارایی‌های بصری برند، تبلیغات، ارائه و شبکه‌های اجتماعی را تولید می‌کند.",
    ),
    WorkforceRoleTemplate(
        slug="ai-software-developer",
        role_code="ai_software_developer",
        name="AI Software Developer",
        name_fa="توسعه‌دهنده نرم‌افزار هوش مصنوعی",
        description="Implements product changes, fixes, integrations, tests, and routine engineering work.",
        description_fa="تغییرات محصول، رفع اشکال، یکپارچه‌سازی، تست و کارهای مهندسی معمول را انجام می‌دهد.",
    ),
    WorkforceRoleTemplate(
        slug="ai-trader",
        role_code="ai_trader",
        name="AI Trader",
        name_fa="معامله‌گر هوش مصنوعی",
        description="Performs market research, risk analysis, trading-plan preparation, and order staging within explicit limits.",
        description_fa="در محدوده‌های صریح، پژوهش بازار، تحلیل ریسک، آماده‌سازی برنامه معاملاتی و آماده‌سازی سفارش برای بررسی را انجام می‌دهد.",
    ),
)


def list_workforce_roles() -> list[dict]:
    return [asdict(role) for role in WORKFORCE_ROLES]


def list_workforce_role_templates() -> list[dict]:
    return [asdict(template) for template in WORKFORCE_ROLE_TEMPLATES]


def get_workforce_role(code: str) -> WorkforceRole:
    for role in WORKFORCE_ROLES:
        if role.code == code:
            return role
    raise KeyError(f"Unknown AI workforce role: {code}")


def get_workforce_role_template(role_code: str) -> WorkforceRoleTemplate:
    for template in WORKFORCE_ROLE_TEMPLATES:
        if template.role_code == role_code:
            return template
    raise KeyError(f"No first-party workforce role template: {role_code}")


def get_workforce_capability_contract(role_code: str, operation: str) -> WorkforceCapabilityContract:
    role = get_workforce_role(role_code)
    for contract in role.capability_contract:
        if contract.operation == operation:
            return contract
    raise KeyError(f"No capability contract for workforce operation: {role_code}:{operation}")


def workforce_template_capability_contract(role_code: str) -> dict:
    """Return the template-level binding required for a catalog workforce role."""
    role = get_workforce_role(role_code)
    return {
        "workforce_role_code": role.code,
        "workforce_capability_contract": workforce_capability_contract_snapshot(role.code),
    }


def workforce_capability_contract_snapshot(role_code: str) -> list[dict]:
    """Return a stable JSON-safe snapshot of the role's capability contracts."""
    role = get_workforce_role(role_code)
    return [asdict(contract) for contract in role.capability_contract]


def assert_workforce_capability_contract_snapshot(role_code: str, snapshot: object) -> None:
    """Fail closed when a provisioned workforce role carries a stale contract snapshot."""
    if snapshot is None:
        return
    if not isinstance(snapshot, list) or snapshot != workforce_capability_contract_snapshot(role_code):
        raise ValidationAppError(
            "Workforce capability contract is stale; operation denied",
            details={"role": role_code},
        )


def assert_workforce_tool_binding(role_code: str, operation: str, tool_name: str) -> None:
    """Require an explicit role-operation-to-tool binding before tool execution."""
    contract = get_workforce_capability_contract(role_code, operation)
    if not contract.tool_names:
        raise ValidationAppError(
            "Workforce operation has no approved Tool Registry binding",
            details={
                "role": role_code,
                "operation": operation,
                "capability": contract.capability_code,
            },
        )
    if tool_name not in contract.tool_names:
        raise ValidationAppError(
            "Tool is not bound to the requested workforce capability",
            details={
                "role": role_code,
                "operation": operation,
                "capability": contract.capability_code,
                "tool": tool_name,
            },
        )


def is_operation_allowed(role_code: str, operation: str, *, manager_delegated: bool = False) -> bool:
    role = get_workforce_role(role_code)
    if operation in role.approval_required_operations:
        return False
    if operation not in role.allowed_routine_operations:
        return False
    if role.code == "ai_internal_manager":
        return manager_delegated
    return True

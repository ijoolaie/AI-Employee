from app.services.sales_readiness_service import TEMPLATES, _validate_template_tools


EXPECTED_CODES = {
    "sales_assistant",
    "support_agent",
    "order_assistant",
    "catalog_assistant",
    "report_analyst",
    "document_analyst",
    "finance_assistant",
}


def test_customer_employee_template_catalog_is_curated_and_complete():
    assert {template["code"] for template in TEMPLATES} == EXPECTED_CODES
    assert len(TEMPLATES) == 7

    required = {
        "name",
        "name_fa",
        "description",
        "description_fa",
        "purpose",
        "purpose_fa",
        "category",
        "category_fa",
        "input_contract",
        "input_contract_fa",
        "output_contract",
        "output_contract_fa",
        "dependencies",
        "dependencies_fa",
        "example",
        "example_fa",
        "version",
        "min_platform_version",
        "allowed_tools",
        "rules",
        "prompt_template",
    }
    for template in TEMPLATES:
        assert required <= template.keys()
        assert template["allowed_tools"]
        assert template["dependencies"]
        assert template["dependencies_fa"]
        assert template["version"]
        assert template["min_platform_version"]


def test_customer_employee_templates_reference_only_registered_tools():
    for template in TEMPLATES:
        _validate_template_tools(template)

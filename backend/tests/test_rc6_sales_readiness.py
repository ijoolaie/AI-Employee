from app.services.sales_readiness_service import list_templates

def test_rc6_templates_have_guardrails():
    templates=list_templates()
    assert len(templates) >= 3
    assert all(t["rules"] for t in templates)
    assert all("allowed_tools" in t for t in templates)

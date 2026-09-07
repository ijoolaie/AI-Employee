from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_template import AgentTemplate, AgentTemplateStatus


def test_agent_template_has_governance_contract() -> None:
    columns = AgentTemplate.__table__.c
    assert {"agent_definition_id", "risk_tier", "permission_policy", "approval_policy", "evaluation_policy", "install_policy"} <= set(columns.keys())
    assert "status" in columns
    assert {item.value for item in AgentTemplateStatus} == {"draft", "evaluating", "published", "suspended", "retired"}


def test_agent_instance_has_sponsor_and_template_lineage() -> None:
    columns = AgentInstance.__table__.c
    assert {"agent_template_id", "sponsor_user_id", "risk_tier", "permission_policy", "approval_policy"} <= set(columns.keys())
    assert {item.value for item in AgentInstanceStatus} >= {"enabled", "disabled", "draining", "suspended", "retired"}

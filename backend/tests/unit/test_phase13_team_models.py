from uuid import uuid4

from app.models.team_definition import TeamDefinition
from app.models.team_version import TeamVersion


def test_team_definition_is_tenant_scoped() -> None:
    team = TeamDefinition(
        tenant_id=uuid4(),
        slug="support-team",
        name="Support Team",
    )
    assert team.tenant_id is not None
    assert TeamDefinition.__table__.c.tenant_id.nullable is False
    assert TeamDefinition.__table__.c.enabled.default.arg is True


def test_team_definition_has_tenant_slug_uniqueness_contract() -> None:
    constraints = {constraint.name for constraint in TeamDefinition.__table__.constraints}
    assert "uq_team_definitions_tenant_slug" in constraints


def test_team_version_is_unique_per_team_and_contract_fields_are_present() -> None:
    version = TeamVersion(
        team_id=uuid4(),
        version=1,
        member_agent_definition_ids=[str(uuid4())],
        roles={"lead": "agent"},
        execution_policy={"approval_required": True},
    )
    assert version.version == 1
    assert version.allowed_tools is None
    constraints = {constraint.name for constraint in TeamVersion.__table__.constraints}
    assert "uq_team_versions_team_version" in constraints

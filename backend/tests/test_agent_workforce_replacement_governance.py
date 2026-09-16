from pathlib import Path

from app.models.agent_workforce_proposal import AgentWorkforceProposalKind


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_replacement_proposal_kind_is_explicit() -> None:
    assert AgentWorkforceProposalKind.REPLACEMENT.value == "replacement"
    assert AgentWorkforceProposalKind.STAFFING.value == "staffing"


def test_replacement_proposal_persists_predecessor_lineage() -> None:
    source = (BACKEND_ROOT / "app" / "models" / "agent_workforce_proposal.py").read_text(encoding="utf-8")
    assert "replacement_for_agent_instance_id" in source
    assert "replacement_cutover_at" in source
    assert "replacement_retired_at" in source


def test_replacement_workflow_has_distinct_governed_steps() -> None:
    source = (BACKEND_ROOT / "app" / "services" / "agent_workforce_replacement_service.py").read_text(encoding="utf-8")
    assert "create_replacement_proposal" in source
    assert "prepare_replacement_cutover" in source
    assert "cutover_replacement" in source
    assert "AgentWorkforceProposalKind.REPLACEMENT" in source
    assert "agent_workforce.replacement.proposal_submitted" in source
    assert "agent_workforce.replacement.cutover_prepared" in source
    assert "agent_workforce.replacement.cutover_completed" in source


def test_replacement_cutover_requires_drain_and_zero_active_work() -> None:
    source = (BACKEND_ROOT / "app" / "services" / "agent_workforce_replacement_service.py").read_text(encoding="utf-8")
    assert "predecessor.status != AgentInstanceStatus.DRAINING" in source
    assert 'capacity["active_work_items"]' in source
    assert "Replacement predecessor still has active WorkItems" in source


def test_replacement_activation_reuses_full_governance_gate() -> None:
    source = (BACKEND_ROOT / "app" / "services" / "agent_workforce_replacement_service.py").read_text(encoding="utf-8")
    assert "activate_provisioned_proposal" in source
    assert "proposal.status != AgentWorkforceProposalStatus.PROVISIONED" in source
    assert "cutover_by_user_id" in source


def test_replacement_api_is_registered_and_permission_gated() -> None:
    router = (BACKEND_ROOT / "app" / "api" / "v1" / "router.py").read_text(encoding="utf-8")
    replacement_api = (BACKEND_ROOT / "app" / "api" / "v1" / "agent_workforce_replacements.py").read_text(encoding="utf-8")
    migration = next((BACKEND_ROOT / "alembic" / "versions").glob("p8_09_agent_workforce_replacements.py"))
    migration_source = migration.read_text(encoding="utf-8")
    assert "agent_workforce_replacements" in router
    assert 'prefix="/agent-workforce/replacements"' in replacement_api
    assert 'require_permission("agent_workforce.replace")' in replacement_api
    assert '"agent_workforce.replace"' in migration_source

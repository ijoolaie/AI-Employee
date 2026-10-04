from pathlib import Path


def test_payout_execution_status_has_explicit_provider_outcomes():
    from app.models.skill_marketplace_payout_proposal import (
        SkillMarketplacePayoutExecutionStatus,
    )

    assert {item.value for item in SkillMarketplacePayoutExecutionStatus} == {
        "not_executed",
        "pending",
        "accepted",
        "failed",
        "unknown",
    }


def test_payout_proposal_model_records_provider_evidence_without_authorizing_execution():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "models"
        / "skill_marketplace_payout_proposal.py"
    ).read_text(encoding="utf-8")

    for field in (
        "idempotency_key",
        "provider_payout_id",
        "provider_event_id",
        "failure_code",
        "retryable",
        "executed",
        "external_execution",
    ):
        assert field in source

    assert "SkillMarketplacePayoutExecutionStatus" in source


def test_payout_execution_migration_removes_single_state_constraint():
    source = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "w16_skill_marketplace_payout_proposal.py"
    ).read_text(encoding="utf-8")

    assert "pending" in source
    assert "accepted" in source
    assert "failed" in source
    assert "unknown" in source
    assert "ck_skill_marketplace_payout_proposal_not_executed" not in source


def test_payout_execution_ledger_does_not_add_transport_calls():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "models"
        / "skill_marketplace_payout_proposal.py"
    ).read_text(encoding="utf-8")

    assert "httpx" not in source
    assert "stripe" not in source.lower()

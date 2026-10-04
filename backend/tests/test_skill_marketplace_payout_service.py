from pathlib import Path


def test_payout_proposal_requires_and_snapshots_seller_destination():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")

    assert "SkillMarketplacePayoutDestinationStatus.ACTIVE" in source
    assert "with_for_update()" in source
    assert "destination.seller_tenant_id != settlement.seller_tenant_id" in source
    assert "destination_id=destination.id" in source
    assert "destination_provider=destination.provider" in source
    assert "destination_ref=destination.destination_ref" in source
    assert '"destination": "bound_snapshot"' in source


def test_payout_proposal_destination_binding_is_not_provider_execution():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")
    assert "httpx" not in source
    assert "stripe" not in source.lower()
    assert 'provider="none"' in source
    assert "NOT_EXECUTED" in source


def test_payout_proposal_model_has_historical_destination_snapshot():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "models"
        / "skill_marketplace_payout_proposal.py"
    ).read_text(encoding="utf-8")
    assert "destination_id" in source
    assert "destination_provider" in source
    assert "destination_ref" in source
    assert "skill_marketplace_payout_destinations.id" in source


def test_destination_binding_uses_a_new_migration_after_destination_ledger():
    source = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "w16_skill_marketplace_payout_destination_binding.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "w16_skill_mkt_payout_destination"' in source
    assert "destination_id" in source
    assert "destination_provider" in source
    assert "destination_ref" in source
    assert "fk_skill_marketplace_payout_proposal_destination" in source

    original = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "w16_skill_marketplace_payout_proposal.py"
    ).read_text(encoding="utf-8")
    assert "destination_id" not in original


def test_payout_proposal_snapshots_destination_at_creation():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")
    proposal_source = source.split("proposal = SkillMarketplacePayoutProposal(", 1)[1].split("db.add(proposal)", 1)[0]
    assert "destination_id=destination.id" in proposal_source
    assert "destination_provider=destination.provider" in proposal_source
    assert "destination_ref=destination.destination_ref" in proposal_source

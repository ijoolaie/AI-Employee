from decimal import Decimal

def test_payout_proposal_is_explicitly_non_executing():
    from app.models.skill_marketplace_payout_proposal import (
        SkillMarketplacePayoutExecutionStatus,
        SkillMarketplacePayoutProposalStatus,
    )
    assert SkillMarketplacePayoutProposalStatus.PROPOSED.value == "proposed"
    assert SkillMarketplacePayoutProposalStatus.CANCELLED.value == "cancelled"
    assert SkillMarketplacePayoutExecutionStatus.NOT_EXECUTED.value == "not_executed"


def test_payout_proposal_service_is_platform_admin_scoped():
    from pathlib import Path
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")
    assert 'tenant_kind == "vendor"' in source
    assert "is_platform_admin.is_(True)" in source
    assert 'provider="none"' in source
    assert "NOT_EXECUTED" in source
    assert "not_calculated" in source


def test_payout_proposal_uses_seller_net_only():
    from pathlib import Path
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")
    assert "settlement.seller_net_amount" in source
    assert "settlement.platform_fee_amount" not in source


def test_payout_proposal_does_not_introduce_provider_http_calls():
    from pathlib import Path
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")
    assert "httpx" not in source
    assert "stripe" not in source.lower()

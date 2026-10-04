def test_marketplace_settlement_does_not_execute_payout_or_tax():
    from app.models.skill_marketplace_settlement import (
        SkillMarketplacePayoutStatus,
        SkillMarketplaceSettlementStatus,
    )
    assert SkillMarketplaceSettlementStatus.RECORDED.value == "recorded"
    assert SkillMarketplacePayoutStatus.NOT_EXECUTED.value == "not_executed"

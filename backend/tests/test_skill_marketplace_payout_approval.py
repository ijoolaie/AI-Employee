def test_payout_approval_is_separate_from_proposal():
    from app.models.skill_marketplace_payout_approval import SkillMarketplacePayoutApprovalStatus
    assert SkillMarketplacePayoutApprovalStatus.APPROVED.value == "approved"
    assert SkillMarketplacePayoutApprovalStatus.REJECTED.value == "rejected"

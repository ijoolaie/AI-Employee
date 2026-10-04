def test_payout_approval_is_separate_and_single_decision_scoped():
    from app.models.skill_marketplace_payout_approval import (
        SkillMarketplacePayoutApproval,
        SkillMarketplacePayoutApprovalStatus,
    )

    assert SkillMarketplacePayoutApprovalStatus.APPROVED.value == "approved"
    assert SkillMarketplacePayoutApprovalStatus.REJECTED.value == "rejected"
    unique_sets = {
        frozenset(constraint.columns.keys())
        for constraint in SkillMarketplacePayoutApproval.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert frozenset({"proposal_id"}) in unique_sets

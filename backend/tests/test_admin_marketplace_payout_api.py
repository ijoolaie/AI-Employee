def test_marketplace_payout_proposal_routes_use_platform_admin_context():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "admin.py"
    ).read_text(encoding="utf-8")
    assert '@router.post("/marketplace/settlements/{settlement_id}/payout-proposal"' in source
    assert 'ctx: PlatformAdminContext' in source
    assert "create_payout_proposal" in source
    assert "list_payout_proposals" in source


def test_marketplace_payout_approval_and_execution_routes_require_explicit_permissions():
    assert 'require_marketplace_payout_approver' in r_source()
    assert 'skill_marketplace.payout.approve' in r_source()
    assert 'require_marketplace_payout_executor' in r_source()
    assert 'skill_marketplace.payout.execute' in r_source()
    assert '@router.post(' in r_source()


def r_source() -> str:
    from pathlib import Path
    return (
        Path(__file__).resolve().parents[1]
        / "app"
        / "api"
        / "v1"
        / "admin.py"
    ).read_text(encoding="utf-8")

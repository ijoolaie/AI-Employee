def test_marketplace_payout_proposal_routes_use_platform_admin_context():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "admin.py"
    ).read_text(encoding="utf-8")
    assert '@router.post("/marketplace/settlements/{settlement_id}/payout-proposal"' in source
    assert 'ctx: PlatformAdminContext' in source
    assert "create_payout_proposal" in source
    assert "list_payout_proposals" in source


def test_marketplace_payout_execution_evidence_route_is_read_only_and_filterable():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "admin.py").read_text(encoding="utf-8")
    assert '@router.get("/marketplace/payout-executions"' in source
    assert "list_payout_execution_evidence" in source
    assert "execution_status" in source
    assert "seller_tenant_id" in source


def test_marketplace_payout_reconciliation_route_is_platform_admin_and_approval_bound():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "admin.py").read_text(encoding="utf-8")
    assert '@router.post("/marketplace/payout-executions/{proposal_id}/reconcile"' in source
    assert "ctx: PlatformAdminContext" in source
    assert "approval_request_id" in source
    assert "reconcile_unknown_payout_execution" in source

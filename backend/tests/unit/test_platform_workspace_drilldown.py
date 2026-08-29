from app.services.platform_workspace_drilldown import workspace_drilldown


def test_workspace_drilldown_projects_safe_fields_only():
    summary = {
        "attention": [{
            "work_item_id": "42",
            "correlation_id": "corr-42",
            "status": "failed",
            "priority": "high",
            "reason": "executor failure",
            "evidence_ref": "evidence-42",
            "audit_ref": "audit-42",
            "secret_value": "must not leak",
        }]
    }
    result = workspace_drilldown(summary, work_item_id="42", role="operator")
    assert result["correlation_id"] == "corr-42"
    assert result["evidence_ref"] == "evidence-42"
    assert result["audit_ref"] == "audit-42"
    assert "secret_value" not in result
    assert result["read_only"] is False


def test_workspace_drilldown_viewer_is_read_only():
    summary = {"attention": [{"work_item_id": "42", "correlation_id": "corr-42"}]}
    result = workspace_drilldown(summary, work_item_id="42", role="viewer")
    assert result["read_only"] is True


def test_workspace_drilldown_rejects_unknown_role_and_missing_item():
    summary = {"attention": [{"work_item_id": "42"}]}
    assert workspace_drilldown(summary, work_item_id="42", role="unknown") is None
    assert workspace_drilldown(summary, work_item_id="missing", role="operator") is None

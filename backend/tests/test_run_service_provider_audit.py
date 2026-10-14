from app.services.run_service import _provider_audit_metadata, _tool_audit_status


def test_unknown_provider_outcome_is_durable_and_not_audited_as_success():
    tool_result = {
        "provider": "github",
        "operation": "git_branch",
        "provider_execution": "outcome_unknown",
        "executed": False,
        "external_side_effect": True,
        "provider_reason": "GitHub branch creation outcome unknown: HTTP 503",
        "arguments": {"token": "must-not-be-copied"},
    }

    assert _tool_audit_status(tool_result, "success") == "outcome_unknown"
    assert _provider_audit_metadata(tool_result) == {
        "provider": "github",
        "operation": "git_branch",
        "provider_execution": "outcome_unknown",
        "executed": False,
        "external_side_effect": True,
        "provider_reason": "GitHub branch creation outcome unknown: HTTP 503",
    }


def test_provider_audit_metadata_bounds_reason_and_leaves_other_tools_unchanged():
    result = {
        "provider_execution": "outcome_unknown",
        "provider_reason": "x" * 700,
        "untrusted_payload": {"secret": "not copied"},
    }

    metadata = _provider_audit_metadata(result)
    assert len(metadata["provider_reason"]) == 500
    assert "untrusted_payload" not in metadata
    assert _tool_audit_status({"status": "success"}, "success") == "success"
    assert _provider_audit_metadata({"status": "success"}) == {}

def test_reconciled_provider_outcome_is_not_audited_as_execution_success():
    tool_result = {
        "provider": "github",
        "operation": "git_branch",
        "provider_execution": "reconciled",
        "executed": False,
        "external_side_effect": True,
        "provider_reason": '{"branch":"feature/example","prior_outcome":"unknown"}',
    }

    assert _tool_audit_status(tool_result, "success") == "reconciled"
    assert _provider_audit_metadata(tool_result) == {
        "provider": "github",
        "operation": "git_branch",
        "provider_execution": "reconciled",
        "executed": False,
        "external_side_effect": True,
        "provider_reason": '{"branch":"feature/example","prior_outcome":"unknown"}',
    }


from app.services.platform_workspace_view import workspace_view


def test_workspace_view_is_compact_and_safe():
    result = workspace_view({
        "overview": {
            "total_work_items": 3,
            "lifecycle": {"failed": 1},
            "executor_mix": {"agent": 2},
            "waiting_approval": 1,
            "failed": 1,
            "secret_value": "must not be exposed",
        },
        "attention": [{"work_item_id": "1"}],
        "action_readiness": [{"work_item_id": "1", "actions": ["retry"]}],
        "attention_count": 1,
        "actionable_count": 1,
    })
    assert result["total_work_items"] == 3
    assert "secret_value" not in result
    assert result["actionable_count"] == 1

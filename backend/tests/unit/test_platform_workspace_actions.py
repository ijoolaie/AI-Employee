from app.services.platform_workspace_actions import workspace_actions


def test_workspace_actions_are_role_aware():
    summary = {"action_readiness": [{"work_item_id": "1", "actions": ["retry", "review_approval"]}]}
    assert all(x["enabled"] for x in workspace_actions(summary, role="operator"))
    assert not any(x["enabled"] for x in workspace_actions(summary, role="viewer"))


def test_workspace_actions_ignore_unknown_actions():
    summary = {"action_readiness": [{"work_item_id": "1", "actions": ["unknown", "retry"]}]}
    result = workspace_actions(summary, role="operator")
    assert [x["action"] for x in result] == ["retry"]

from pathlib import Path


def test_approved_tool_resume_uses_transactional_outbox():
    source = (Path(__file__).parents[1] / "app/api/v1/approvals.py").read_text()

    assert "await outbox_service.enqueue(" in source
    assert 'kind="agent.run.execute"' in source
    assert 'dedupe_key=f"agent.run.execute:approval:{approval.id}"' in source
    assert 'payload={"run_id": str(approval.run_id)' not in source
    assert "execute_run_task.delay" not in source


def test_approved_tool_resume_carries_tenant_context():
    source = (Path(__file__).parents[1] / "app/api/v1/approvals.py").read_text()

    assert '"run_id": str(approval.run_id)' in source
    assert '"tenant_id": str(ctx.tenant_id)' in source

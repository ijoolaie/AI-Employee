from pathlib import Path


def test_run_creation_uses_transactional_outbox():
    source = (
        Path(__file__).parents[1] / "app/api/v1/runs.py"
    ).read_text(encoding="utf-8")

    assert "await outbox_service.enqueue(" in source
    assert 'kind="agent.run.execute"' in source
    assert '"run_id": str(run.id)' in source
    assert '"tenant_id": str(ctx.tenant_id)' in source
    assert 'dedupe_key=f"agent.run.execute:run:{run.id}"' in source
    assert "execute_run_task.delay" not in source


def test_run_creation_outbox_documents_transaction_boundary():
    source = (
        Path(__file__).parents[1] / "app/api/v1/runs.py"
    ).read_text(encoding="utf-8")

    assert "same transaction as the Run" in source

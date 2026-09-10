from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app" / "services" / "agent_run_governance_bootstrap.py"


def test_production_run_execution_admission_locks_run_row() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "select(Run).where(Run.id == run_id).with_for_update()" in source
    assert "Serialize every production Run execution admission" in source


def test_non_agent_runs_share_the_same_serialized_admission_boundary() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    lock_pos = source.index("with_for_update()")
    non_agent_fallback_pos = source.index("run.agent_instance_id is None")
    canonical_execution_pos = source.index(
        "return await original_execute_run(db, run_id=run_id)"
    )

    assert lock_pos < non_agent_fallback_pos < canonical_execution_pos

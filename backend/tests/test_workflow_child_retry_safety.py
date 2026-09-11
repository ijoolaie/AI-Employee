from pathlib import Path


SOURCE = Path(__file__).parents[1] / "app/services/workflow_service.py"
LEASE_SOURCE = Path(__file__).parents[1] / "app/services/workflow_execution_lease.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_sequential_child_retry_fails_closed_after_linked_run_exists() -> None:
    source = _source()
    assert '"WORKFLOW_CHILD_RETRY_UNSAFE"' in source
    assert "Linked employee Run ended with status" in source
    assert "refusing to create a replacement Run" in source


def test_parallel_child_retry_fails_closed_before_creating_a_second_child() -> None:
    source = _source()
    lease_source = LEASE_SOURCE.read_text(encoding="utf-8")
    assert "WORKFLOW_CHILD_RETRY_UNSAFE" in source
    assert "employee_run_id" in source
    assert "if employee_run_id:" in source
    assert "Linked employee Run ended with status" in source
    assert "for attempt in range(1, max_attempts + 1)" not in source
    assert "recover_parallel_branch_execution_lease" in lease_source

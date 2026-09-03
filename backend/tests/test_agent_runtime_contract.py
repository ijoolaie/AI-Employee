import pytest

from app.agents.runtime_contract import AgentRuntimeContract, RetryPolicy


def _contract(**overrides):
    values = {
        "tenant_id": "tenant-1",
        "run_id": "run-1",
        "employee_id": "employee-1",
        "employee_version_id": "version-1",
        "input_data": {"message": "hello"},
        "allowed_tools": frozenset({"calculator"}),
        "permissions": frozenset({"run.execute"}),
    }
    values.update(overrides)
    return AgentRuntimeContract(**values)


def test_runtime_contract_validates_complete_identity_and_controls():
    contract = _contract()
    contract.validate()
    assert contract.evidence_context() == {
        "tenant_id": "tenant-1",
        "run_id": "run-1",
        "employee_id": "employee-1",
        "employee_version_id": "version-1",
        "approval_id": None,
    }


@pytest.mark.parametrize("field", ["tenant_id", "run_id", "employee_id", "employee_version_id"])
def test_runtime_contract_requires_identity(field):
    with pytest.raises(ValueError, match="runtime identity is incomplete"):
        _contract(**{field: ""}).validate()


def test_runtime_contract_requires_approval_id_for_explicit_approval_state():
    with pytest.raises(ValueError, match="approval_id is required"):
        _contract(approval_state="granted").validate()


def test_runtime_contract_rejects_invalid_retry_policy():
    with pytest.raises(ValueError, match="max_attempts"):
        _contract(retry=RetryPolicy(max_attempts=0)).validate()

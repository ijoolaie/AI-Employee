from app.agents.runtime_contract import AgentRuntimeContract, RetryPolicy
from app.agents.safety_gate import SafetyGateEvidence, evaluate_safety_gate


def _contract(**overrides):
    values = {
        "tenant_id": "tenant-a",
        "run_id": "run-1",
        "employee_id": "employee-1",
        "employee_version_id": "version-1",
        "input_data": {"case": "safe"},
        "approval_state": "not_required",
        "timeout_seconds": 30,
        "retry": RetryPolicy(max_attempts=1),
    }
    values.update(overrides)
    return AgentRuntimeContract(**values)


def _evidence(**overrides):
    values = {
        "tenant_isolation": True,
        "permission_enforcement": True,
        "approval_enforcement": True,
        "timeout_safety": True,
        "retry_safety": True,
        "evidence_integrity": True,
        "negative_path_coverage": True,
        "observed_tenant_ids": frozenset({"tenant-a"}),
        "evidence": {
            "tenant_id": "tenant-a",
            "run_id": "run-1",
            "employee_id": "employee-1",
            "employee_version_id": "version-1",
            "outcome": "succeeded",
            "passed": True,
        },
    }
    values.update(overrides)
    return SafetyGateEvidence(**values)


def test_safety_gate_passes_complete_safe_evidence():
    result = evaluate_safety_gate(_contract(), _evidence())
    assert result.passed is True
    assert result.failed_checks == ()
    assert result.contract_version == "phase-13.7/v1"


def test_safety_gate_rejects_cross_tenant_observation():
    result = evaluate_safety_gate(
        _contract(), _evidence(observed_tenant_ids=frozenset({"tenant-a", "tenant-b"}))
    )
    assert result.passed is False
    assert "tenant_isolation" in result.failed_checks


def test_safety_gate_requires_granted_approval_when_contract_requires_it():
    result = evaluate_safety_gate(
        _contract(approval_state="pending", approval_id="approval-1"), _evidence()
    )
    assert result.passed is False
    assert "approval_enforcement" in result.failed_checks


def test_safety_gate_rejects_sensitive_evidence_keys():
    result = evaluate_safety_gate(
        _contract(), _evidence(evidence={"tenant_id": "tenant-a", "prompt": "do it"})
    )
    assert result.passed is False
    assert "sensitive_evidence" in result.failed_checks


def test_safety_gate_fails_closed_for_missing_probe():
    result = evaluate_safety_gate(_contract(), _evidence(timeout_safety=False))
    assert result.passed is False
    assert "timeout_safety" in result.failed_checks


def test_safety_gate_rejects_unexpected_evidence_fields():
    result = evaluate_safety_gate(
        _contract(), _evidence(evidence={"tenant_id": "tenant-a", "secret_ref": "credential"})
    )
    assert result.passed is False
    assert "evidence_integrity" in result.failed_checks

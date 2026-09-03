from app.services.agent_evaluation import evaluate_run


def test_evaluation_is_deterministic_and_exact():
    expected = {"equals": {"status": "ok", "count": 2}}
    first = evaluate_run(
        expected=expected,
        result={"count": 2, "status": "ok"},
        evidence={"git_sha": "a" * 64},
        run_status="passed",
    )
    second = evaluate_run(
        expected=expected,
        result={"status": "ok", "count": 2},
        evidence={"git_sha": "a" * 64},
        run_status="passed",
    )
    assert first == second
    assert first.passed is True
    assert first.score == 1.0


def test_evaluation_rejects_result_mismatch_and_missing_evidence():
    outcome = evaluate_run(
        expected={"equals": {"status": "ok"}, "evidence_keys": ["git_sha"]},
        result={"status": "failed"},
        evidence={},
        run_status="failed",
    )
    assert outcome.passed is False
    assert "result does not match expected value" in outcome.reasons
    assert "missing required evidence key: git_sha" in outcome.reasons


def test_evaluation_requires_approval_for_gated_case():
    blocked = evaluate_run(
        expected={"approval_required": True},
        result={"status": "ok"},
        evidence={},
        run_status="passed",
        approval_state="not_required",
    )
    allowed = evaluate_run(
        expected={"approval_required": True},
        result={"status": "ok"},
        evidence={},
        run_status="passed",
        approval_state="approved",
    )
    assert blocked.passed is False
    assert allowed.passed is True


def test_evaluation_has_safety_negative_for_sensitive_payloads():
    outcome = evaluate_run(
        expected={"required_keys": ["status"]},
        result={"status": "ok", "prompt": "do something"},
        evidence={"memory_text": "sensitive"},
        run_status="passed",
    )
    assert outcome.passed is False
    assert "evaluation payload contains a forbidden sensitive key" in outcome.reasons


def test_non_terminal_run_cannot_pass_evaluation():
    outcome = evaluate_run(
        expected={"equals": {"status": "ok"}},
        result={"status": "ok"},
        evidence={},
        run_status="running",
    )
    assert outcome.passed is False
    assert "evaluation requires a terminal run" in outcome.reasons

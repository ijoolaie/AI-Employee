from app.services.customer_dashboard_service import _office_count_key, _office_presentation_state


def test_office_presentation_state_precedence_and_mapping():
    cases = [
        (False, "running", False, "IDLE", "idle"),
        (True, "running", True, "WAITING_APPROVAL", "waiting"),
        (True, "running", False, "WORKING", "working"),
        (True, "failed", False, "ESCALATED", "escalated"),
        (True, "cancelled", False, "BLOCKED", "blocked"),
        (True, "success", False, "IDLE", "idle"),
        (True, None, False, "IDLE", "idle"),
    ]

    for is_active, run_status, waiting, expected_state, expected_count_key in cases:
        state = _office_presentation_state(
            is_active=is_active,
            run_status=run_status,
            waiting_approval=waiting,
        )
        assert state == expected_state
        assert _office_count_key(state) == expected_count_key

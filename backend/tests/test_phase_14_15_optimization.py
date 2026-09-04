import pytest

from app.services.optimization_service import budget_status, cost_per_work_item, recommend_worker_count


def test_worker_sizing_adds_headroom():
    assert recommend_worker_count(
        observed_items_per_minute=10,
        target_items_per_minute=25,
        utilization_target=0.70,
    ) == 4


def test_worker_sizing_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        recommend_worker_count(observed_items_per_minute=0, target_items_per_minute=1)
    with pytest.raises(ValueError):
        recommend_worker_count(observed_items_per_minute=1, target_items_per_minute=1, utilization_target=0)


def test_cost_per_work_item_is_safe_for_empty_period():
    assert cost_per_work_item(total_cost_usd=12.50, work_items=0) == 0.0
    assert cost_per_work_item(total_cost_usd=12.50, work_items=5) == 2.5


def test_budget_state_transitions():
    assert budget_status(used_runs=50, run_limit=100, used_tokens=40, token_limit=100)["state"] == "ok"
    assert budget_status(used_runs=85, run_limit=100, used_tokens=40, token_limit=100)["state"] == "warning"
    assert budget_status(used_runs=100, run_limit=100, used_tokens=40, token_limit=100)["state"] == "exhausted"
    exhausted = budget_status(used_runs=120, run_limit=100, used_tokens=40, token_limit=100)
    assert exhausted["remaining_runs"] == 0

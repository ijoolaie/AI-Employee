from app.services.workload_balancing import (
    BALANCING_CONTRACT_VERSION,
    AgentLoadSnapshot,
    BalancingPolicy,
    QueueSnapshot,
    calculate_queue_pressure,
    recommend_rebalance,
)


def test_queue_pressure_is_zero_for_empty_queue():
    assert calculate_queue_pressure(QueueSnapshot(ready_items=0), total_available_slots=4) == 0.0


def test_queue_pressure_increases_when_capacity_is_exhausted():
    queue = QueueSnapshot(ready_items=4, oldest_ready_age_seconds=2.0, priority_weight=0.5)
    assert calculate_queue_pressure(queue, total_available_slots=0) == 5.0


def test_recommend_rebalance_selects_available_capacity_deterministically():
    queue = QueueSnapshot(ready_items=3, oldest_ready_age_seconds=10.0)
    agents = [
        AgentLoadSnapshot("z", active_work_items=1, max_concurrency=3),
        AgentLoadSnapshot("a", active_work_items=1, max_concurrency=3),
        AgentLoadSnapshot("busy", active_work_items=2, max_concurrency=2),
    ]

    decision = recommend_rebalance(queue, agents, BalancingPolicy(min_ready_items=2, min_queue_age_seconds=5))

    assert decision.contract_version == BALANCING_CONTRACT_VERSION
    assert decision.target_agent_instance_id == "a"
    assert "recommendation_only" in decision.rationale
    assert decision.candidates_considered == 3


def test_recommendation_is_suppressed_below_threshold():
    decision = recommend_rebalance(
        QueueSnapshot(ready_items=1, oldest_ready_age_seconds=100),
        [AgentLoadSnapshot("agent-1", max_concurrency=2)],
        BalancingPolicy(min_ready_items=2),
    )

    assert decision.target_agent_instance_id is None
    assert decision.rationale == ("queue_below_rebalance_threshold",)


def test_recommendation_fails_closed_without_capacity():
    decision = recommend_rebalance(
        QueueSnapshot(ready_items=5, oldest_ready_age_seconds=10),
        [AgentLoadSnapshot("agent-1", active_work_items=2, max_concurrency=2)],
        BalancingPolicy(min_ready_items=1),
    )

    assert decision.target_agent_instance_id is None
    assert decision.rationale == ("no_available_agent_capacity", "fail_closed")


def test_disabled_agent_is_not_selected():
    decision = recommend_rebalance(
        QueueSnapshot(ready_items=5, oldest_ready_age_seconds=10),
        [
            AgentLoadSnapshot("disabled", max_concurrency=4, accepting_work=False),
            AgentLoadSnapshot("available", max_concurrency=1),
        ],
        BalancingPolicy(),
    )

    assert decision.target_agent_instance_id == "available"

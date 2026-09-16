"""Deterministic, recommendation-only queue-aware workload balancing.

Stage 9 increment 2 evaluates live queue pressure against already-authorized
Agent capacity. It emits a bounded recommendation and never mutates WorkItems,
Agent lifecycle, permissions, approval policy, or budgets.
"""
from __future__ import annotations

from dataclasses import dataclass, field


BALANCING_CONTRACT_VERSION = "agent-workload-balancing-v1"


@dataclass(frozen=True)
class QueueSnapshot:
    """Tenant-scoped queue state supplied by the authoritative execution layer."""

    ready_items: int = 0
    oldest_ready_age_seconds: float = 0.0
    priority_weight: float = 1.0


@dataclass(frozen=True)
class AgentLoadSnapshot:
    """Already-authorized Agent capacity and current load."""

    agent_instance_id: str
    active_work_items: int = 0
    max_concurrency: int = 1
    accepting_work: bool = True

    @property
    def available_slots(self) -> int:
        return max(self.max_concurrency - self.active_work_items, 0)


@dataclass(frozen=True)
class BalancingPolicy:
    """Explicit bounds for recommendation generation."""

    min_ready_items: int = 1
    min_queue_age_seconds: float = 0.0
    max_recommendations: int = 1


@dataclass(frozen=True)
class WorkloadBalanceDecision:
    """Explainable recommendation; execution remains with existing services."""

    contract_version: str
    queue_pressure: float
    target_agent_instance_id: str | None
    rationale: tuple[str, ...] = field(default_factory=tuple)
    candidates_considered: int = 0


def calculate_queue_pressure(queue: QueueSnapshot, total_available_slots: int) -> float:
    """Calculate normalized queue pressure without side effects."""
    ready = max(queue.ready_items, 0)
    slots = max(total_available_slots, 0)
    age_factor = max(queue.oldest_ready_age_seconds, 0.0) * max(queue.priority_weight, 0.0)
    if ready == 0:
        return 0.0
    if slots == 0:
        return float(ready) + age_factor
    return (ready / slots) + age_factor


def recommend_rebalance(
    queue: QueueSnapshot,
    agents: list[AgentLoadSnapshot],
    policy: BalancingPolicy,
) -> WorkloadBalanceDecision:
    """Recommend a deterministic target Agent when queue pressure warrants it."""
    available = sum(agent.available_slots for agent in agents if agent.accepting_work)
    pressure = calculate_queue_pressure(queue, available)

    if queue.ready_items < max(policy.min_ready_items, 0):
        return WorkloadBalanceDecision(
            contract_version=BALANCING_CONTRACT_VERSION,
            queue_pressure=pressure,
            target_agent_instance_id=None,
            rationale=("queue_below_rebalance_threshold",),
            candidates_considered=0,
        )
    if queue.oldest_ready_age_seconds < max(policy.min_queue_age_seconds, 0.0):
        return WorkloadBalanceDecision(
            contract_version=BALANCING_CONTRACT_VERSION,
            queue_pressure=pressure,
            target_agent_instance_id=None,
            rationale=("queue_age_below_rebalance_threshold",),
            candidates_considered=0,
        )

    eligible = [agent for agent in agents if agent.accepting_work and agent.available_slots > 0]
    if not eligible:
        return WorkloadBalanceDecision(
            contract_version=BALANCING_CONTRACT_VERSION,
            queue_pressure=pressure,
            target_agent_instance_id=None,
            rationale=("no_available_agent_capacity", "fail_closed"),
            candidates_considered=len(agents),
        )

    selected = sorted(
        eligible,
        key=lambda agent: (-agent.available_slots, agent.active_work_items, agent.agent_instance_id),
    )[0]
    return WorkloadBalanceDecision(
        contract_version=BALANCING_CONTRACT_VERSION,
        queue_pressure=pressure,
        target_agent_instance_id=selected.agent_instance_id,
        rationale=(
            "queue_pressure_requires_rebalance",
            "available_capacity_selected",
            "deterministic_tie_breaking",
            "recommendation_only",
        ),
        candidates_considered=len(agents),
    )

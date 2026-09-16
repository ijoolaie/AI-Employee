"""Deterministic, governance-bounded workforce optimization primitives.

Stage 9 starts with recommendation-only optimization. The kernel may select an
eligible Agent/model candidate from already-authorized inputs, but it never
changes lifecycle state, permissions, budgets, or approval policy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


OPTIMIZATION_CONTRACT_VERSION = "agent-optimization-v1"


@dataclass(frozen=True)
class OptimizationPolicy:
    """Tenant/application bounds that optimization must not cross."""

    max_risk_tier: int = 0
    max_cost_usd: float | None = None
    require_all_capabilities: bool = True
    allow_model_fallback: bool = True


@dataclass(frozen=True)
class TaskProfile:
    """Normalized work requirements supplied by an already-authorized caller."""

    required_capabilities: FrozenSet[str] = frozenset()
    risk_tier: int = 0
    estimated_cost_usd: float = 0.0
    latency_weight: float = 0.0
    cost_weight: float = 0.0


@dataclass(frozen=True)
class AgentCandidate:
    """An executable Agent candidate with governance already established."""

    agent_instance_id: str
    capabilities: FrozenSet[str] = frozenset()
    risk_tier: int = 0
    active_load: int = 0
    max_concurrency: int = 1
    fitness: float = 0.0


@dataclass(frozen=True)
class ModelCandidate:
    """A provider/model option exposed by the existing provider layer."""

    model: str
    supported_risk_tier: int = 0
    estimated_cost_usd: float = 0.0
    quality: float = 0.0
    latency_ms: float = 0.0


@dataclass(frozen=True)
class OptimizationDecision:
    """Explainable recommendation; execution remains with existing services."""

    contract_version: str
    agent_instance_id: str
    model: str | None
    rationale: tuple[str, ...] = field(default_factory=tuple)
    agent_candidates_considered: int = 0
    model_candidates_considered: int = 0


def _agent_key(candidate: AgentCandidate, task: TaskProfile) -> tuple[float, int, int, str]:
    remaining_capacity = max(candidate.max_concurrency - candidate.active_load, 0)
    capability_bonus = len(candidate.capabilities & task.required_capabilities)
    return (
        -candidate.fitness,
        -remaining_capacity,
        -capability_bonus,
        candidate.agent_instance_id,
    )


def select_agent(
    task: TaskProfile,
    candidates: list[AgentCandidate],
    policy: OptimizationPolicy,
) -> tuple[AgentCandidate | None, tuple[str, ...]]:
    """Select an eligible candidate without mutating workforce state."""
    eligible: list[AgentCandidate] = []
    for candidate in candidates:
        if candidate.risk_tier > policy.max_risk_tier or candidate.risk_tier < task.risk_tier:
            continue
        if candidate.active_load >= max(candidate.max_concurrency, 0):
            continue
        if policy.require_all_capabilities and not task.required_capabilities.issubset(candidate.capabilities):
            continue
        eligible.append(candidate)

    if not eligible:
        return None, ("no_governed_agent_candidate",)

    selected = sorted(eligible, key=lambda item: _agent_key(item, task))[0]
    rationale = (
        "capability_requirements_satisfied",
        "capacity_available",
        "risk_within_policy",
        "fitness_and_capacity_tie_breaking",
    )
    return selected, rationale


def _model_key(candidate: ModelCandidate, task: TaskProfile) -> tuple[float, float, float, str]:
    quality = candidate.quality * max(1.0 - task.cost_weight, 0.0)
    cost_penalty = candidate.estimated_cost_usd * max(task.cost_weight, 0.0)
    latency_penalty = candidate.latency_ms * max(task.latency_weight, 0.0)
    return (-quality + cost_penalty + latency_penalty, candidate.estimated_cost_usd, candidate.latency_ms, candidate.model)


def select_model(
    task: TaskProfile,
    candidates: list[ModelCandidate],
    policy: OptimizationPolicy,
) -> tuple[ModelCandidate | None, tuple[str, ...]]:
    """Select a model only inside explicit risk and cost bounds."""
    eligible = [
        candidate
        for candidate in candidates
        if candidate.supported_risk_tier >= task.risk_tier
        and candidate.supported_risk_tier <= policy.max_risk_tier
        and (policy.max_cost_usd is None or candidate.estimated_cost_usd <= policy.max_cost_usd)
    ]
    if not eligible:
        return None, ("no_governed_model_candidate",)

    selected = sorted(eligible, key=lambda item: _model_key(item, task))[0]
    return selected, (
        "risk_within_policy",
        "cost_within_policy",
        "task_cost_latency_weights_applied",
    )


def optimize(
    task: TaskProfile,
    agents: list[AgentCandidate],
    models: list[ModelCandidate],
    policy: OptimizationPolicy,
) -> OptimizationDecision | None:
    """Produce a deterministic recommendation for an already-authorized task."""
    agent, agent_rationale = select_agent(task, agents, policy)
    if agent is None:
        return None

    model, model_rationale = select_model(task, models, policy)
    if model is None and not policy.allow_model_fallback:
        return None

    return OptimizationDecision(
        contract_version=OPTIMIZATION_CONTRACT_VERSION,
        agent_instance_id=agent.agent_instance_id,
        model=model.model if model else None,
        rationale=agent_rationale + model_rationale,
        agent_candidates_considered=len(agents),
        model_candidates_considered=len(models),
    )

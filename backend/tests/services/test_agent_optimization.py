from app.services.agent_optimization import (
    OPTIMIZATION_CONTRACT_VERSION,
    AgentCandidate,
    ModelCandidate,
    OptimizationPolicy,
    TaskProfile,
    optimize,
    select_agent,
    select_model,
)


def test_select_agent_requires_capabilities_capacity_and_risk_bounds():
    task = TaskProfile(required_capabilities=frozenset({"crm", "email"}), risk_tier=2)
    policy = OptimizationPolicy(max_risk_tier=2)
    candidates = [
        AgentCandidate("busy", frozenset({"crm", "email"}), 2, active_load=1, max_concurrency=1, fitness=1.0),
        AgentCandidate("missing-capability", frozenset({"crm"}), 2, active_load=0, max_concurrency=1, fitness=9.0),
        AgentCandidate("eligible", frozenset({"crm", "email"}), 2, active_load=0, max_concurrency=1, fitness=0.5),
        AgentCandidate("too-risky", frozenset({"crm", "email"}), 3, active_load=0, max_concurrency=1, fitness=99.0),
    ]

    selected, rationale = select_agent(task, candidates, policy)

    assert selected is not None
    assert selected.agent_instance_id == "eligible"
    assert "capacity_available" in rationale
    assert "risk_within_policy" in rationale


def test_select_agent_is_deterministic_for_equal_candidates():
    task = TaskProfile(required_capabilities=frozenset({"support"}), risk_tier=1)
    policy = OptimizationPolicy(max_risk_tier=1)
    candidates = [
        AgentCandidate("z", frozenset({"support"}), 1, fitness=1.0),
        AgentCandidate("a", frozenset({"support"}), 1, fitness=1.0),
    ]

    selected, _ = select_agent(task, candidates, policy)

    assert selected is not None
    assert selected.agent_instance_id == "a"


def test_select_model_respects_risk_and_cost_policy():
    task = TaskProfile(risk_tier=2, cost_weight=1.0)
    policy = OptimizationPolicy(max_risk_tier=2, max_cost_usd=0.05)
    candidates = [
        ModelCandidate("expensive", supported_risk_tier=2, estimated_cost_usd=0.20, quality=10.0),
        ModelCandidate("cheap", supported_risk_tier=2, estimated_cost_usd=0.02, quality=7.0),
        ModelCandidate("low-risk", supported_risk_tier=1, estimated_cost_usd=0.01, quality=9.0),
    ]

    selected, rationale = select_model(task, candidates, policy)

    assert selected is not None
    assert selected.model == "cheap"
    assert "cost_within_policy" in rationale


def test_optimize_is_recommendation_only_and_exposes_contract():
    task = TaskProfile(required_capabilities=frozenset({"sales"}), risk_tier=1, cost_weight=0.5)
    agents = [AgentCandidate("agent-1", frozenset({"sales"}), 1, fitness=0.8)]
    models = [ModelCandidate("model-a", supported_risk_tier=1, estimated_cost_usd=0.03, quality=0.9)]
    policy = OptimizationPolicy(max_risk_tier=1, max_cost_usd=0.10)

    decision = optimize(task, agents, models, policy)

    assert decision is not None
    assert decision.contract_version == OPTIMIZATION_CONTRACT_VERSION
    assert decision.agent_instance_id == "agent-1"
    assert decision.model == "model-a"
    assert decision.agent_candidates_considered == 1
    assert decision.model_candidates_considered == 1


def test_optimize_fails_closed_when_no_agent_is_eligible():
    task = TaskProfile(required_capabilities=frozenset({"finance"}), risk_tier=2)
    agents = [AgentCandidate("agent-1", frozenset({"sales"}), 2)]
    models = [ModelCandidate("model-a", supported_risk_tier=2, estimated_cost_usd=0.01)]

    assert optimize(task, agents, models, OptimizationPolicy(max_risk_tier=2)) is None


def test_optimize_fails_closed_when_model_is_required_but_outside_policy():
    task = TaskProfile(required_capabilities=frozenset({"finance"}), risk_tier=2)
    agents = [AgentCandidate("agent-1", frozenset({"finance"}), 2)]
    models = [ModelCandidate("model-a", supported_risk_tier=2, estimated_cost_usd=1.0)]
    policy = OptimizationPolicy(max_risk_tier=2, max_cost_usd=0.10, allow_model_fallback=False)

    assert optimize(task, agents, models, policy) is None

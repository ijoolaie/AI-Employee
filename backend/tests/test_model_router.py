from types import SimpleNamespace

import pytest

from app.ai.model_router import AIModelRouter, RoutingContext
from app.ai.providers.registry import get_provider


def _settings(**overrides):
    values = {
        "ai_router_enabled": True,
        "ai_router_allowed_providers": ["lm_studio", "anthropic"],
        "ai_router_candidates": [
            {
                "provider": "lm_studio",
                "model": "local-model",
                "priority": 10,
                "cost_tier": 1,
                "quality_tier": 1,
                "latency_tier": 1,
                "supports_tools": True,
                "supports_vision": False,
                "supports_json": True,
            },
            {
                "provider": "anthropic",
                "model": "cloud-model",
                "priority": 20,
                "cost_tier": 3,
                "quality_tier": 3,
                "latency_tier": 2,
                "supports_tools": True,
                "supports_vision": True,
                "supports_json": True,
            },
        ],
        "ai_router_task_preferences": {"reasoning": ["anthropic", "lm_studio"]},
        "ai_router_anthropic_model": "cloud-model",
        "ai_default_provider": "lm_studio",
        "ai_default_model": "local-model",
        "anthropic_api_key": "test-key",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_router_prefers_operator_task_order():
    router = AIModelRouter(settings=_settings())
    decision = router.select(RoutingContext(task="reasoning"), requested_model="local-model")
    assert decision.provider == "anthropic"
    assert decision.model == "cloud-model"
    assert decision.task == "reasoning"
    assert "requested_model_overridden_by_router=true" in decision.reason


def test_router_filters_candidates_by_capability_and_cost():
    router = AIModelRouter(settings=_settings())
    decision = router.select(
        RoutingContext(
            task="vision",
            requires_vision=True,
            max_cost_tier=3,
        )
    )
    assert decision.provider == "anthropic"


def test_router_fails_closed_when_no_candidate_matches():
    router = AIModelRouter(settings=_settings())
    with pytest.raises(RuntimeError, match="No operator-approved"):
        router.select(RoutingContext(task="vision", requires_vision=True, max_cost_tier=1))


def test_router_respects_operator_provider_allowlist():
    router = AIModelRouter(
        settings=_settings(ai_router_allowed_providers=["lm_studio"])
    )
    decision = router.select(RoutingContext(task="reasoning"))
    assert decision.provider == "lm_studio"


def test_provider_registry_rejects_unknown_provider():
    with pytest.raises(RuntimeError, match="Unsupported AI provider"):
        get_provider("not-configured")


def test_router_does_not_use_runtime_provider_name():
    router = AIModelRouter(settings=_settings())
    decision = router.select(
        RoutingContext(task="general"),
        requested_model="anything-from-request",
    )
    assert decision.provider in {"lm_studio", "anthropic"}


def test_settings_expose_router_and_embedding_configuration():
    from app.core.config import Settings

    settings = Settings(app_env="test")
    assert settings.ai_router_enabled is False
    assert settings.ai_router_allowed_providers == ["lm_studio"]
    assert settings.ai_embedding_model == "text-embedding-nomic-embed-text-v1.5"

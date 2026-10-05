"""Deterministic, provider-agnostic model routing for the AI Gateway.

The router chooses a provider/model *before* crossing an external provider
boundary. It never performs a retry or provider fallback after a call has
started; ambiguous provider outcomes remain governed by the existing durable
AIProviderCall fence.

Runtime request data is not allowed to select an arbitrary provider. The
operator configures the provider/model candidates and optional task
preferences. This module only ranks those configured candidates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


TASK_DEFAULT = "general"
TASK_TOOL_CALLING = "tool_calling"
TASK_REASONING = "reasoning"
TASK_RAG = "rag"
TASK_MEMORY = "memory_extraction"
TASK_PLANNING = "planning"
TASK_VISION = "vision"
TASK_STRUCTURED = "structured_extraction"


@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    priority: int = 100
    cost_tier: int = 1
    quality_tier: int = 1
    latency_tier: int = 1
    supports_tools: bool = True
    supports_vision: bool = False
    supports_json: bool = True


@dataclass(frozen=True)
class RoutingContext:
    task: str = TASK_DEFAULT
    requires_tools: bool = False
    requires_vision: bool = False
    requires_json: bool = False
    sensitivity: str = "normal"
    max_cost_tier: int | None = None


@dataclass(frozen=True)
class RoutingDecision:
    provider: str
    model: str
    task: str
    reason: str
    candidates_considered: int


def _candidate_from_config(raw: dict[str, Any]) -> ModelCandidate:
    provider = str(raw.get("provider", "")).strip().lower()
    model = str(raw.get("model", "")).strip()
    if not provider or not model:
        raise ValueError("AI router candidates require provider and model")

    def integer(name: str, default: int) -> int:
        value = raw.get(name, default)
        if isinstance(value, bool):
            raise ValueError(f"AI router candidate {name} must be an integer")
        try:
            value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"AI router candidate {name} must be an integer") from exc
        if value < 1:
            raise ValueError(f"AI router candidate {name} must be positive")
        return value

    return ModelCandidate(
        provider=provider,
        model=model,
        priority=integer("priority", 100),
        cost_tier=integer("cost_tier", 1),
        quality_tier=integer("quality_tier", 1),
        latency_tier=integer("latency_tier", 1),
        supports_tools=bool(raw.get("supports_tools", True)),
        supports_vision=bool(raw.get("supports_vision", False)),
        supports_json=bool(raw.get("supports_json", True)),
    )


class AIModelRouter:
    """Select one operator-approved provider/model using deterministic rules."""

    policy_version = "model-router-v1"

    def __init__(self, *, settings=None):
        self.settings = settings or get_settings()

    def enabled(self) -> bool:
        return bool(self.settings.ai_router_enabled)

    def _candidates(self) -> list[ModelCandidate]:
        configured = self.settings.ai_router_candidates or []
        if configured:
            return [_candidate_from_config(item) for item in configured]

        # Backward-compatible local-first fallback. This is deliberately small:
        # new external providers must be added through explicit operator config.
        candidates = [
            ModelCandidate(
                provider=self.settings.ai_default_provider.strip().lower(),
                model=self.settings.ai_default_model,
                priority=100,
                cost_tier=1,
                quality_tier=1,
                latency_tier=1,
                supports_tools=True,
                supports_json=True,
            )
        ]
        if self.settings.anthropic_api_key:
            candidates.append(
                ModelCandidate(
                    provider="anthropic",
                    model=self.settings.ai_router_anthropic_model,
                    priority=200,
                    cost_tier=3,
                    quality_tier=3,
                    latency_tier=2,
                    supports_tools=True,
                    supports_json=True,
                )
            )
        return candidates

    def select(self, context: RoutingContext, *, requested_model: str | None = None) -> RoutingDecision:
        candidates = self._candidates()
        allowed = {
            item.strip().lower()
            for item in (self.settings.ai_router_allowed_providers or [])
            if item and item.strip()
        }
        if allowed:
            candidates = [candidate for candidate in candidates if candidate.provider in allowed]

        task_preferences = self.settings.ai_router_task_preferences or {}
        preferred = [
            str(provider).strip().lower()
            for provider in task_preferences.get(context.task, [])
            if str(provider).strip()
        ]
        if preferred:
            rank = {provider: index for index, provider in enumerate(preferred)}
            candidates.sort(key=lambda c: (rank.get(c.provider, len(rank) + 100), c.priority))
        else:
            candidates.sort(key=lambda c: c.priority)

        filtered: list[ModelCandidate] = []
        for candidate in candidates:
            if context.requires_tools and not candidate.supports_tools:
                continue
            if context.requires_vision and not candidate.supports_vision:
                continue
            if context.requires_json and not candidate.supports_json:
                continue
            if context.max_cost_tier is not None and candidate.cost_tier > context.max_cost_tier:
                continue
            filtered.append(candidate)

        if not filtered:
            raise RuntimeError(
                "No operator-approved AI model candidate satisfies the routing requirements"
            )

        selected = filtered[0]
        reason = (
            f"policy={self.policy_version};task={context.task};"
            f"provider={selected.provider};candidate_rank={candidates.index(selected) + 1}"
        )
        if requested_model and requested_model != selected.model:
            reason += ";requested_model_overridden_by_router=true"

        return RoutingDecision(
            provider=selected.provider,
            model=selected.model,
            task=context.task,
            reason=reason,
            candidates_considered=len(filtered),
        )

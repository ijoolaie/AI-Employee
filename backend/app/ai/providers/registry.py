"""Provider registry/factory.

The AI Gateway depends on the provider interface, not a concrete provider.
"""
from __future__ import annotations

from app.ai.providers.base import AIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.deterministic_provider import DeterministicProvider
from app.ai.providers.lm_studio_provider import LMStudioProvider
from app.core.config import get_settings


def get_provider(provider: str) -> AIProvider:
    """Resolve only named, code-registered providers; unknown names fail closed."""
    settings = get_settings()
    provider = provider.strip().lower()
    if provider in {"lm_studio", "lmstudio", "local"}:
        return LMStudioProvider(
            base_url=settings.lm_studio_base_url,
            api_key=settings.lm_studio_api_key,
        )
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "deterministic":
        return DeterministicProvider()
    raise RuntimeError(f"Unsupported AI provider: {provider}")


def get_default_provider() -> AIProvider:
    settings = get_settings()
    return get_provider(settings.ai_default_provider)

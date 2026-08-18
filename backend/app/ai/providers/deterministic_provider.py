"""Deterministic AI provider used only by the Compose E2E certification stack.

It exercises the real AI Gateway and Run worker without requiring an external
model service. Production defaults never select this provider.
"""
from __future__ import annotations

from app.ai.providers.base import AIProvider
from app.ai.schemas import ChatRequest, ChatResult


class DeterministicProvider:
    name = "deterministic"

    async def chat(self, request: ChatRequest) -> ChatResult:
        user_messages = [m.content for m in request.messages if m.role == "user" and m.content]
        prompt = user_messages[-1] if user_messages else ""
        return ChatResult(
            content=f"Deterministic certification result: {prompt}",
            prompt_tokens=max(1, len(prompt.split())),
            completion_tokens=5,
            stop_reason="stop",
            raw={"provider": self.name, "certification": True},
        )

    def estimate_cost_usd(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0

"""Provider interface. New providers implement this and register in
app.ai.providers.registry — the Gateway never imports a concrete provider
directly (10_AI_Core §3.1: "یکسان‌سازی رابط", Provider-Agnostic)."""

from __future__ import annotations

from typing import Protocol

from app.ai.schemas import ChatRequest, ChatResult


class AIProvider(Protocol):
    name: str

    async def chat(self, request: ChatRequest) -> ChatResult:
        ...

    def estimate_cost_usd(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        ...

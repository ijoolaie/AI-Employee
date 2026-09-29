"""Deterministic AI provider used only by the Compose E2E certification stack.

It exercises the real AI Gateway and Run worker without requiring an external
model service. Production defaults never select this provider.
"""
from __future__ import annotations

from app.ai.providers.base import AIProvider
from app.ai.schemas import ChatRequest, ChatResult, ToolCall


class DeterministicProvider:
    name = "deterministic"
    # Certification provider has no external exactly-once or reconciliation
    # boundary; the gateway's durable fence remains authoritative.
    supports_idempotency = False
    supports_reconciliation = False

    async def chat(self, request: ChatRequest) -> ChatResult:
        user_messages = [m.content for m in request.messages if m.role == "user" and m.content]
        prompt = user_messages[-1] if user_messages else ""

        # The deterministic provider is E2E-only. When the certification stack
        # exposes a governed Workforce tool, emit one deterministic tool call
        # so the real Gateway -> Run -> Celery -> ToolRegistry path can be
        # exercised without an external model service. Production providers
        # are unchanged.
        if request.tools and not any(message.role == "tool" for message in request.messages):
            tool = next(
                (item for item in request.tools if item.name == "workforce_market_research"),
                None,
            )
            if tool is not None:
                return ChatResult(
                    content="",
                    prompt_tokens=max(1, len(prompt.split())),
                    completion_tokens=5,
                    stop_reason="tool_calls",
                    raw={"provider": self.name, "certification": True, "e2e_tool_call": True},
                    tool_calls=[
                        ToolCall(
                            id="e2e-workforce-market-research-1",
                            name=tool.name,
                            arguments={"symbols": ["AAPL"], "horizon_days": 30},
                        )
                    ],
                )

        tool_messages = [message for message in request.messages if message.role == "tool"]
        return ChatResult(
            content=(
                "Deterministic workforce certification result: tool execution verified."
                if tool_messages
                else f"Deterministic certification result: {prompt}"
            ),
            prompt_tokens=max(1, len(prompt.split())),
            completion_tokens=5,
            stop_reason="stop",
            raw={"provider": self.name, "certification": True},
        )

    def estimate_cost_usd(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0

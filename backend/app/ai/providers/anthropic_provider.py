"""Anthropic provider — the single provider wired in v1 (10_AI_Core §3.2,
CHANGELOG_PACKAGE_v1.1 decision #4: "multi-provider design from day one;
only one Provider connected initially").

Pricing table is illustrative and must be kept in sync with Anthropic's
published rates before this is used for real billing — see
19_Finance for how cost figures feed the business model.
"""

from __future__ import annotations

import httpx
import json

from app.ai.providers.base import AIProvider
from app.ai.schemas import ChatRequest, ChatResult, ToolCall
from app.core.config import get_settings

settings = get_settings()

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# USD per 1M tokens (prompt, completion). Placeholder table — confirm
# against Anthropic's current pricing before wiring real billing.
_PRICING_PER_MILLION: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.8, 4.0),
    "claude-opus-4-8": (15.0, 75.0),
}
_DEFAULT_PRICING = (3.0, 15.0)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.anthropic_api_key

    async def chat(self, request: ChatRequest) -> ChatResult:
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not configured — set it in .env before making live calls"
            )

        system_messages = [m.content for m in request.messages if m.role == "system"]
        turn_messages = []
        for m in request.messages:
            if m.role == "system":
                continue
            if m.role == "assistant" and m.tool_calls:
                blocks = []
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                blocks.extend(
                    {"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments}
                    for tc in m.tool_calls
                )
                turn_messages.append({"role": "assistant", "content": blocks})
            elif m.role == "tool":
                turn_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.tool_call_id,
                        "content": m.content,
                    }],
                })
            else:
                turn_messages.append({"role": m.role, "content": m.content})

        payload: dict = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": turn_messages,
        }
        if system_messages:
            payload["system"] = "\n\n".join(system_messages)
        if request.tools:
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in request.tools
            ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        tool_calls = []
        for block in content_blocks:
            if block.get("type") != "tool_use":
                continue
            arguments = block.get("input", {})
            if not isinstance(arguments, dict):
                arguments = json.loads(arguments)
            tool_calls.append(
                ToolCall(
                    id=str(block.get("id")),
                    name=str(block.get("name")),
                    arguments=arguments,
                )
            )
        usage = data.get("usage", {})

        return ChatResult(
            content=text,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            stop_reason=data.get("stop_reason"),
            raw=data,
            tool_calls=tool_calls,
        )

    def estimate_cost_usd(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        prompt_rate, completion_rate = _PRICING_PER_MILLION.get(model, _DEFAULT_PRICING)
        return (prompt_tokens / 1_000_000) * prompt_rate + (
            completion_tokens / 1_000_000
        ) * completion_rate


def get_default_provider() -> AIProvider:
    return AnthropicProvider()

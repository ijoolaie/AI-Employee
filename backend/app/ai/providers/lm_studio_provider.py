"""LM Studio provider using its OpenAI-compatible local HTTP API.

LM Studio is local-only by default in development, so provider cost is zero.
The provider remains behind the provider-agnostic AI Gateway interface.
"""
from __future__ import annotations

import httpx
import json

from app.ai.providers.base import AIProvider
from app.ai.schemas import ChatRequest, ChatResult, ChatMessage, ToolCall
from app.core.config import get_settings


class LMStudioProvider:
    name = "lm_studio"

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.lm_studio_base_url).rstrip("/")
        self.api_key = api_key or settings.lm_studio_api_key

    async def chat(self, request: ChatRequest) -> ChatResult:
        messages = []
        for m in request.messages:
            item: dict = {"role": m.role, "content": m.content or None}
            if m.role == "assistant" and m.tool_calls:
                item["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    }
                    for tc in m.tool_calls
                ]
            if m.role == "tool":
                item["tool_call_id"] = m.tool_call_id
                item["content"] = m.content
            messages.append(item)

        payload: dict = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.tools:
            payload["tools"] = [
                {"type": "function", "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                }}
                for t in request.tools
            ]

        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("LM Studio returned no choices")
        message = choices[0].get("message", {})
        content = message.get("content") or ""
        tool_calls: list[ToolCall] = []
        for raw_call in message.get("tool_calls", []) or []:
            function = raw_call.get("function", {}) or {}
            raw_args = function.get("arguments", "{}")
            try:
                arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"LM Studio returned invalid tool arguments: {exc}") from exc
            if not isinstance(arguments, dict):
                raise RuntimeError("LM Studio returned non-object tool arguments")
            tool_calls.append(
                ToolCall(
                    id=str(raw_call.get("id") or "tool-call"),
                    name=str(function.get("name") or ""),
                    arguments=arguments,
                )
            )
        usage = data.get("usage", {}) or {}

        return ChatResult(
            content=content,
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            stop_reason=choices[0].get("finish_reason"),
            raw=data,
            tool_calls=tool_calls,
        )

    def estimate_cost_usd(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        # Local LM Studio inference has no provider API charge.
        return 0.0


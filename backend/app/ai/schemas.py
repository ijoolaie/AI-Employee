"""Provider-agnostic request/response shapes for the AI Gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatMessage:
    role: Role
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class ChatRequest:
    messages: list[ChatMessage]
    model: str
    max_tokens: int = 1024
    temperature: float = 1.0
    tools: list[ToolDefinition] = field(default_factory=list)


@dataclass
class ChatResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    stop_reason: str | None = None
    raw: dict[str, Any] | None = None
    latency_ms: int = 0
    cost_usd: float = 0.0
    tool_calls: list[ToolCall] = field(default_factory=list)

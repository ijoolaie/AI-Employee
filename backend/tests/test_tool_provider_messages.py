import json

import pytest

from app.ai.providers.lm_studio_provider import LMStudioProvider
from app.ai.schemas import ChatMessage, ChatRequest, ToolCall


@pytest.mark.asyncio
async def test_lm_studio_serializes_assistant_tool_call(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "calculator", "arguments": '{"expression":"2+2"}'},
                        }],
                    },
                    "finish_reason": "tool_calls",
                }],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            }

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            captured["payload"] = json
            return Response()

    monkeypatch.setattr("app.ai.providers.lm_studio_provider.httpx.AsyncClient", Client)

    provider = LMStudioProvider(base_url="http://127.0.0.1:1234/v1")
    result = await provider.chat(ChatRequest(
        model="google/gemma-4-e4b",
        messages=[
            ChatMessage(role="assistant", content="", tool_calls=[ToolCall("call_1", "calculator", {"expression": "2+2"})]),
            ChatMessage(role="tool", content=json.dumps({"result": 4}), tool_call_id="call_1"),
        ],
        tools=[],
    ))

    messages = captured["payload"]["messages"]
    assert messages[0]["tool_calls"][0]["function"]["name"] == "calculator"
    assert messages[1]["role"] == "tool"
    assert result.tool_calls[0].arguments == {"expression": "2+2"}

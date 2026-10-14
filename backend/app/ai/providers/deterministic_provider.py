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
            supported_tools = (
                "workforce_market_research",
                "workforce_produce_article",
                "workforce_produce_social_caption",
                "workforce_create_visual_asset",
                "workforce_revise_visual_asset",
                "workforce_content_qa",
                "workforce_customer_context",
                "workforce_workspace_create_file",
                "workforce_keyword_research",
                "workforce_qa_test_plan",
            )
            tool = next((item for name in supported_tools for item in request.tools if item.name == name), None)
            if tool is not None:
                fixtures = {
                    "workforce_market_research": (
                        "e2e-workforce-market-research-1",
                        {"symbols": ["AAPL"], "horizon_days": 30},
                    ),
                    "workforce_produce_article": (
                        "e2e-workforce-produce-article-1",
                        {
                            "title": "Semantic E2E governed article",
                            "body": "Deterministic article created by the governed Content Producer WorkItem lifecycle.",
                            "metadata": {"source": "workforce-semantic-real-stack-e2e"},
                        },
                    ),
                    "workforce_produce_social_caption": (
                        "e2e-workforce-produce-social-caption-1",
                        {
                            "title": "Semantic E2E governed social caption",
                            "body": "A concise, deterministic launch caption for the product dashboard.",
                            "metadata": {"source": "workforce-semantic-real-stack-e2e"},
                        },
                    ),
                    "workforce_create_visual_asset": (
                        "e2e-workforce-create-visual-asset-1",
                        {
                            "prompt": "Create a clean abstract SaaS launch visual for the product dashboard",
                            "brand_context": "Workforce semantic E2E fixture",
                            "provider": "image-provider",
                        },
                    ),
                    "workforce_revise_visual_asset": (
                        "e2e-workforce-revise-visual-asset-1",
                        {
                            "prompt": "Revise the existing SaaS dashboard launch visual to use a calmer palette",
                            "brand_context": "Workforce semantic E2E fixture",
                            "provider": "image-provider",
                        },
                    ),
                    "workforce_content_qa": (
                        "e2e-workforce-content-qa-1",
                        {
                            "title": "Semantic E2E QA article",
                            "body": "A complete deterministic article body with no placeholder markers.",
                            "metadata": {"source": "workforce-semantic-real-stack-e2e"},
                        },
                    ),
                    "workforce_customer_context": (
                        "e2e-workforce-customer-context-1",
                        {
                            "customer_reference": "customer-e2e-001",
                            "query": "support history and account health",
                            "evidence": ["deterministic certification fixture"],
                            "recommendation": "Review the account health evidence before any customer-facing action.",
                        },
                    ),
                    "workforce_workspace_create_file": (
                        "e2e-workforce-workspace-create-file-1",
                        {
                            "path": "src/semantic-e2e.txt",
                            "content": "Deterministic engineering workspace fixture.",
                        },
                    ),
                    "workforce_keyword_research": (
                        "e2e-workforce-keyword-research-1",
                        {"topic": "SaaS customer acquisition"},
                    ),
                    "workforce_qa_test_plan": (
                        "e2e-workforce-qa-test-plan-1",
                        {
                            "repository": "certification-fixture",
                            "commit_sha": "0000000000000000000000000000000000000000",
                            "test_scope": "full-regression",
                        },
                    ),
                }
                call_id, arguments = fixtures[tool.name]
                return ChatResult(
                    content="",
                    prompt_tokens=max(1, len(prompt.split())),
                    completion_tokens=5,
                    stop_reason="tool_calls",
                    raw={"provider": self.name, "certification": True, "e2e_tool_call": True},
                    tool_calls=[ToolCall(id=call_id, name=tool.name, arguments=arguments)],
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

"""AI Gateway — the single entry point for all model calls."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.registry import get_default_provider
from app.ai.providers.base import AIProvider
from app.ai.schemas import ChatRequest, ChatResult
from app.core.logging import Timer, request_id_var
from app.core.metrics import AI_CALLS, AI_COST, AI_LATENCY, AI_TOKENS
from app.core.telemetry import span
from app.models.ai_provider_call import AIProviderCall
from app.services import audit_service, usage_service

logger = logging.getLogger("app.ai.gateway")


class AIGateway:
    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or get_default_provider()

    async def chat(
        self,
        db: AsyncSession,
        request: ChatRequest,
        *,
        tenant_id: uuid.UUID,
        run_id: uuid.UUID | None = None,
        prompt_version: str | None = None,
        call_metadata: dict | None = None,
    ) -> ChatResult:
        req_id = request_id_var.get()
        status = "success"
        error_message: str | None = None
        result: ChatResult | None = None

        with span("aiep.ai.chat", tenant_id=str(tenant_id), provider=self.provider.name, model=request.model, run_id=str(run_id) if run_id else None) as ai_span:
            with Timer() as timer:
                try:
                    result = await self.provider.chat(request)
                except Exception as exc:  # noqa: BLE001 — recorded, then re-raised
                    status = "error"
                    error_message = str(exc)[:1000]
                    raise
                finally:
                    prompt_tokens = result.prompt_tokens if result else 0
                    completion_tokens = result.completion_tokens if result else 0
                    cost = (
                        self.provider.estimate_cost_usd(request.model, prompt_tokens, completion_tokens)
                        if result else 0.0
                    )
                    latency_ms = max(0, int(timer.elapsed_ms))

                    if result is not None:
                        result.latency_ms = latency_ms
                        result.cost_usd = cost

                    AI_CALLS.labels(self.provider.name, status).inc()
                    AI_LATENCY.labels(self.provider.name).observe(latency_ms / 1000.0)
                    AI_TOKENS.labels(self.provider.name, "prompt").inc(prompt_tokens)
                    AI_TOKENS.labels(self.provider.name, "completion").inc(completion_tokens)
                    AI_COST.labels(self.provider.name).inc(float(cost))
                    if ai_span is not None:
                        ai_span.set_attribute("ai.status", status)
                        ai_span.set_attribute("ai.prompt_tokens", prompt_tokens)
                        ai_span.set_attribute("ai.completion_tokens", completion_tokens)
                        ai_span.set_attribute("ai.cost_usd", float(cost))
                        ai_span.set_attribute("ai.latency_ms", latency_ms)

                    call_log = AIProviderCall(
                        tenant_id=tenant_id, run_id=run_id, provider=self.provider.name,
                        model=request.model, prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens, cost_usd=cost,
                        latency_ms=latency_ms, status=status, error_message=error_message,
                        prompt_version=prompt_version, request_id=req_id, raw_meta=call_metadata or {},
                    )
                    db.add(call_log)
                    await db.flush()

                    usage_key = f"ai.provider_call:{req_id}" if req_id else f"ai.provider_call:{call_log.id}"
                    await usage_service.record_event(
                        db,
                        tenant_id=tenant_id,
                        event_key=usage_key,
                        category="ai_call",
                        quantity=1,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost_usd=cost,
                        source_type="ai_provider_call",
                        source_id=str(call_log.id),
                        metadata={"provider": self.provider.name, "model": request.model, "status": status},
                    )

                    logger.info("ai_provider_call", extra={
                        "provider": self.provider.name, "model": request.model,
                        "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                        "cost_usd": cost, "latency_ms": latency_ms, "status": status,
                        "run_id": str(run_id) if run_id else None,
                    })

                    await audit_service.record(
                        db, action="ai.provider_call", actor_type="system", tenant_id=tenant_id,
                        resource_type="run", resource_id=run_id, status=status, request_id=req_id,
                        metadata={"provider": self.provider.name, "model": request.model,
                                  "cost_usd": cost, "latency_ms": latency_ms,
                                  "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                                  **(call_metadata or {})},
                    )

        return result

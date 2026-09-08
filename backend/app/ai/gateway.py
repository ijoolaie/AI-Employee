"""AI Gateway — the single entry point for all model calls."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.registry import get_default_provider
from app.ai.providers.base import AIProvider
from app.ai.schemas import ChatRequest, ChatResult
from app.core.exceptions import ValidationAppError
from app.core.logging import Timer, request_id_var
from app.core.metrics import AI_CALLS, AI_COST, AI_LATENCY, AI_TOKENS
from app.core.telemetry import span
from app.models.agent_instance import AgentInstance
from app.models.ai_provider_call import AIProviderCall
from app.models.run import Run
from app.services import audit_service, usage_service

logger = logging.getLogger("app.ai.gateway")


async def _reserve_agent_run_budget(db: AsyncSession, *, run_id: uuid.UUID) -> tuple[Run | None, Decimal]:
    """Fail closed before a governed Agent model call when a run budget is configured.

    AgentInstance.budget_policy supports:
      {"max_cost_usd": 1.00, "reservation_usd": 0.10}

    The Run row is locked for the duration of the execution transaction, so
    sequential model turns observe the accumulated persisted cost. A configured
    max without a positive reservation is rejected rather than pretending that
    an unknown provider response can be reserved safely.
    """
    result = await db.execute(
        select(Run, AgentInstance)
        .join(AgentInstance, AgentInstance.id == Run.agent_instance_id)
        .where(Run.id == run_id)
        .with_for_update(of=Run)
    )
    row = result.one_or_none()
    if row is None:
        return None, Decimal("0")

    run, agent = row
    policy = agent.budget_policy or {}
    if "max_cost_usd" not in policy:
        return run, Decimal("0")

    try:
        limit = Decimal(str(policy["max_cost_usd"]))
        reservation = Decimal(str(policy.get("reservation_usd", "0")))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationAppError("Invalid Agent budget policy") from exc

    if limit < 0 or reservation <= 0:
        raise ValidationAppError("Agent budget policy requires non-negative max_cost_usd and positive reservation_usd")

    current = Decimal(str(run.total_cost_usd or 0))
    if current + reservation > limit:
        raise usage_service.UsageLimitExceeded(
            "Agent run cost budget exhausted"
        )
    return run, reservation


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
        budget_run: Run | None = None
        budget_reservation = Decimal("0")

        if run_id is not None:
            budget_run, budget_reservation = await _reserve_agent_run_budget(db, run_id=run_id)

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

                    if budget_run is not None and result is not None:
                        # Persist the actual spend immediately so the next model
                        # turn cannot bypass the run-level budget by relying on
                        # run_service's end-of-run aggregate only.
                        budget_run.total_cost_usd = Decimal(str(budget_run.total_cost_usd or 0)) + Decimal(str(cost))
                        budget_run.total_tokens = int(budget_run.total_tokens or 0) + prompt_tokens + completion_tokens
                        await db.flush()

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
                                  "budget_reservation_usd": float(budget_reservation),
                                  **(call_metadata or {})},
                    )

        return result

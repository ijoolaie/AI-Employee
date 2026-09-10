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
from app.core.database import AsyncSessionLocal
from app.core.exceptions import ValidationAppError
from app.core.logging import Timer, request_id_var
from app.core.metrics import AI_CALLS, AI_COST, AI_LATENCY, AI_TOKENS
from app.core.telemetry import span
from app.models.agent_instance import AgentInstance
from app.models.ai_provider_call import AIProviderCall
from app.models.run import Run
from app.services import audit_service, usage_service

logger = logging.getLogger("app.ai.gateway")


class AIProviderCallAmbiguous(ValidationAppError):
    """A provider call may already have crossed the external execution boundary."""


def _durable_call_id(*, tenant_id: uuid.UUID, run_id: uuid.UUID, model_turn: int) -> uuid.UUID:
    """Return a stable row identity for one logical model turn."""
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"aiep:ai-provider-call:{tenant_id}:{run_id}:{model_turn}",
    )


async def _prepare_durable_call(
    *,
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    model_turn: int,
    provider: str,
    model: str,
    request_id: str | None,
    call_metadata: dict,
) -> uuid.UUID:
    """Commit a durable execution fence before crossing the provider boundary."""
    call_id = _durable_call_id(tenant_id=tenant_id, run_id=run_id, model_turn=model_turn)
    async with AsyncSessionLocal() as durable_db:
        existing = await durable_db.get(AIProviderCall, call_id)
        if existing is not None:
            raise AIProviderCallAmbiguous(
                "AI provider call already crossed the execution boundary; refusing blind replay"
            )
        durable_db.add(
            AIProviderCall(
                id=call_id,
                tenant_id=tenant_id,
                run_id=run_id,
                provider=provider,
                model=model,
                status="in_flight",
                request_id=request_id,
                raw_meta={**call_metadata, "model_turn": model_turn},
            )
        )
        await durable_db.commit()
    return call_id


async def _finalize_durable_call(
    *,
    call_id: uuid.UUID,
    result: ChatResult,
    provider: AIProvider,
    model: str,
    prompt_version: str | None,
    request_id: str | None,
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    call_metadata: dict,
    latency_ms: int,
    status: str,
    error_message: str | None,
) -> None:
    """Persist provider-call accounting independently of the Run transaction."""
    cost = provider.estimate_cost_usd(model, result.prompt_tokens, result.completion_tokens)
    async with AsyncSessionLocal() as durable_db:
        call_log = await durable_db.get(AIProviderCall, call_id)
        if call_log is None:
            raise RuntimeError("Durable AI provider call fence disappeared")
        call_log.prompt_tokens = result.prompt_tokens
        call_log.completion_tokens = result.completion_tokens
        call_log.cost_usd = cost
        call_log.latency_ms = latency_ms
        call_log.status = status
        call_log.error_message = error_message
        call_log.prompt_version = prompt_version
        call_log.request_id = request_id
        call_log.raw_meta = {**(call_log.raw_meta or {}), **call_metadata}
        await durable_db.flush()

        usage_key = f"ai.provider_call:{call_id}"
        await usage_service.record_event(
            durable_db,
            tenant_id=tenant_id,
            event_key=usage_key,
            category="ai_call",
            quantity=1,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            cost_usd=cost,
            source_type="ai_provider_call",
            source_id=str(call_id),
            metadata={"provider": provider.name, "model": model, "status": status},
        )
        await audit_service.record(
            durable_db,
            action="ai.provider_call",
            actor_type="system",
            tenant_id=tenant_id,
            resource_type="run",
            resource_id=run_id,
            status=status,
            request_id=request_id,
            metadata={
                "provider": provider.name,
                "model": model,
                "cost_usd": cost,
                "latency_ms": latency_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                **call_metadata,
            },
        )
        await durable_db.commit()


def _reserve_agent_run_budget_placeholder() -> None:
    """Keep the budget helper below visually separated from durable-call helpers."""


async def _reserve_agent_run_budget(db: AsyncSession, *, run_id: uuid.UUID) -> tuple[Run | None, Decimal]:
    """Fail closed before a governed Agent model call when a run budget is configured."""
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
        raise usage_service.UsageLimitExceeded("Agent run cost budget exhausted")
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
        metadata = call_metadata or {}
        budget_run: Run | None = None
        budget_reservation = Decimal("0")

        if run_id is not None:
            budget_run, budget_reservation = await _reserve_agent_run_budget(db, run_id=run_id)

        durable_call_id: uuid.UUID | None = None
        if run_id is not None:
            model_turn = metadata.get("model_turn")
            if not isinstance(model_turn, int) or model_turn < 0:
                raise ValidationAppError("run-scoped AI calls require a non-negative model_turn")
            durable_call_id = await _prepare_durable_call(
                tenant_id=tenant_id,
                run_id=run_id,
                model_turn=model_turn,
                provider=self.provider.name,
                model=request.model,
                request_id=req_id,
                call_metadata=metadata,
            )

        with span("aiep.ai.chat", tenant_id=str(tenant_id), provider=self.provider.name, model=request.model, run_id=str(run_id) if run_id else None) as ai_span:
            with Timer() as timer:
                try:
                    result = await self.provider.chat(request)
                except Exception as exc:  # noqa: BLE001 — durable fence is marked ambiguous
                    if durable_call_id is not None:
                        async with AsyncSessionLocal() as durable_db:
                            call_log = await durable_db.get(AIProviderCall, durable_call_id)
                            if call_log is not None:
                                call_log.status = "unknown"
                                call_log.error_message = str(exc)[:1000]
                                call_log.raw_meta = {**(call_log.raw_meta or {}), "ambiguous_provider_outcome": True}
                                await durable_db.commit()
                    AI_CALLS.labels(self.provider.name, "unknown").inc()
                    raise

                latency_ms = max(0, int(timer.elapsed_ms))
                result.latency_ms = latency_ms
                cost = self.provider.estimate_cost_usd(request.model, result.prompt_tokens, result.completion_tokens)
                result.cost_usd = cost

                AI_CALLS.labels(self.provider.name, "success").inc()
                AI_LATENCY.labels(self.provider.name).observe(latency_ms / 1000.0)
                AI_TOKENS.labels(self.provider.name, "prompt").inc(result.prompt_tokens)
                AI_TOKENS.labels(self.provider.name, "completion").inc(result.completion_tokens)
                AI_COST.labels(self.provider.name).inc(float(cost))
                if ai_span is not None:
                    ai_span.set_attribute("ai.status", "success")
                    ai_span.set_attribute("ai.prompt_tokens", result.prompt_tokens)
                    ai_span.set_attribute("ai.completion_tokens", result.completion_tokens)
                    ai_span.set_attribute("ai.cost_usd", float(cost))
                    ai_span.set_attribute("ai.latency_ms", latency_ms)

                if durable_call_id is not None:
                    await _finalize_durable_call(
                        call_id=durable_call_id,
                        result=result,
                        provider=self.provider,
                        model=request.model,
                        prompt_version=prompt_version,
                        request_id=req_id,
                        tenant_id=tenant_id,
                        run_id=run_id,
                        call_metadata={"budget_reservation_usd": float(budget_reservation), **metadata},
                        latency_ms=latency_ms,
                        status="success",
                        error_message=None,
                    )
                    if budget_run is not None:
                        budget_run.total_cost_usd = Decimal(str(budget_run.total_cost_usd or 0)) + Decimal(str(cost))
                        budget_run.total_tokens = int(budget_run.total_tokens or 0) + result.prompt_tokens + result.completion_tokens
                        await db.flush()
                else:
                    call_log = AIProviderCall(
                        tenant_id=tenant_id, run_id=run_id, provider=self.provider.name,
                        model=request.model, prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens, cost_usd=cost,
                        latency_ms=latency_ms, status="success", error_message=None,
                        prompt_version=prompt_version, request_id=req_id, raw_meta=metadata,
                    )
                    db.add(call_log)
                    await db.flush()
                    usage_key = f"ai.provider_call:{req_id}" if req_id else f"ai.provider_call:{call_log.id}"
                    await usage_service.record_event(
                        db, tenant_id=tenant_id, event_key=usage_key, category="ai_call", quantity=1,
                        prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
                        cost_usd=cost, source_type="ai_provider_call", source_id=str(call_log.id),
                        metadata={"provider": self.provider.name, "model": request.model, "status": "success"},
                    )
                    await audit_service.record(
                        db, action="ai.provider_call", actor_type="system", tenant_id=tenant_id,
                        resource_type="run", resource_id=run_id, status="success", request_id=req_id,
                        metadata={"provider": self.provider.name, "model": request.model,
                                  "cost_usd": cost, "latency_ms": latency_ms,
                                  "prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens,
                                  "budget_reservation_usd": float(budget_reservation), **metadata},
                    )

        logger.info("ai_provider_call", extra={
            "provider": self.provider.name, "model": request.model,
            "prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens,
            "cost_usd": result.cost_usd, "latency_ms": result.latency_ms, "status": "success",
            "run_id": str(run_id) if run_id else None,
        })
        return result

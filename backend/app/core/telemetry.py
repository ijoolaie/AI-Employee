"""Phase 1 OpenTelemetry bootstrap and reusable span helpers."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from app.core.config import get_settings

_TRACER = None
_PROVIDER = None


def init_telemetry() -> None:
    """Configure OpenTelemetry once, without making telemetry a hard dependency."""
    global _TRACER, _PROVIDER
    if _TRACER is not None:
        return
    settings = get_settings()
    if not settings.otel_enabled:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        resource = Resource.create({
            "service.name": settings.otel_service_name,
            "service.version": "0.2.46",
            "deployment.environment": settings.app_env,
        })
        provider = TracerProvider(resource=resource)
        if settings.otel_exporter_endpoint:
            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint))
            )
        trace.set_tracer_provider(provider)
        _PROVIDER = provider
        _TRACER = trace.get_tracer("aiep")
    except Exception:
        # Observability must never prevent the API/worker from starting.
        _TRACER = False


def get_tracer():
    if _TRACER is None:
        init_telemetry()
    if _TRACER is False:
        return None
    return _TRACER


@contextmanager
def span(name: str, **attributes: object) -> Iterator[object | None]:
    """Start a best-effort span; telemetry failures must never affect business logic."""
    try:
        tracer = get_tracer()
        if tracer is None:
            yield None
            return
        with tracer.start_as_current_span(name) as current:
            for key, value in attributes.items():
                if value is not None:
                    current.set_attribute(key, value)
            yield current
    except Exception:
        # Exporters/SDKs are explicitly non-authoritative operational plumbing.
        yield None


@contextmanager
def agent_runtime_span(**attributes: object) -> Iterator[object | None]:
    """Runtime span with a deliberately narrow, caller-supplied attribute set."""
    allowed = {
        "run.id",
        "tenant.id",
        "employee.id",
        "employee.version.id",
        "approval.state",
        "approval.id",
        "memory.count",
        "memory.employee.version.id",
        "runtime.retryable",
        "runtime.max_attempts",
        "runtime.attempt",
        "runtime.outcome",
        "runtime.failure_category",
        "runtime.timeout",
    }
    safe = {key: value for key, value in attributes.items() if key in allowed}
    with span("aiep.agent.runtime", **safe) as current:
        yield current

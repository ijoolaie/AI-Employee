from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_observability_dependencies_are_declared():
    requirements = (ROOT / "requirements.txt").read_text()
    for package in (
        "prometheus-client",
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-instrumentation-fastapi",
        "opentelemetry-instrumentation-sqlalchemy",
        "opentelemetry-exporter-otlp-proto-http",
    ):
        assert package in requirements


def test_prometheus_surface_contains_phase1_metrics():
    source = (ROOT / "app/core/metrics.py").read_text()
    for metric in (
        "aiep_http_requests_total",
        "aiep_workflow_runs_total",
        "aiep_workflow_steps_total",
        "aiep_ai_provider_calls_total",
        "aiep_ai_cost_usd_total",
        "aiep_outbox_messages",
        "aiep_celery_tasks_total",
        "aiep_redis_broker_queue_depth",
        "aiep_dependency_up",
    ):
        assert metric in source


def test_otel_bootstrap_and_auto_instrumentation_exist():
    telemetry = (ROOT / "app/core/telemetry.py").read_text()
    main = (ROOT / "app/main.py").read_text()
    assert "OTLPSpanExporter" in telemetry
    assert "FastAPIInstrumentor" in main
    assert "SQLAlchemyInstrumentor" in main


def test_manual_ai_workflow_outbox_spans_exist():
    for relative in (
        "app/ai/gateway.py",
        "app/workers/workflow_worker.py",
        "app/workers/run_worker.py",
        "app/workers/outbox_worker.py",
        "app/workers/celery_app.py",
    ):
        assert "span" in (ROOT / relative).read_text()


def test_metrics_reads_celery_queue_from_celery_broker_database():
    main = (ROOT / "app/main.py").read_text()
    assert 'Redis.from_url(settings.celery_broker_url' in main
    assert 'REDIS_QUEUE_DEPTH.labels("celery")' in main

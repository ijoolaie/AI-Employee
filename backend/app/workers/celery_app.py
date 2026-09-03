"""Celery application instance. Run endpoints enqueue onto this; the worker
process is started separately: `celery -A app.workers.celery_app worker -l info`.
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from time import perf_counter
from app.core.metrics import CELERY_TASKS, CELERY_TASK_LATENCY
from app.core.telemetry import get_tracer

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aiep",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.run_worker", "app.workers.workflow_worker", "app.workers.workflow_trigger_worker", "app.workers.outbox_worker", "app.workers.email_worker", "app.workers.test_center_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={"workflow-schedule-tick": {"task": "workflow.schedule_tick", "schedule": 30.0},
        "workflow-approval-expiry": {"task": "workflow.approval_expiry", "schedule": 30.0},
        "workflow-timeout-sweep": {"task": "workflow.timeout_sweep", "schedule": 30.0},
        "test-center-expiration-sweep": {"task": "test_center.expiration_sweep", "schedule": 30.0},
        "outbox-dispatch": {"task": "outbox.dispatch", "schedule": 5.0}},
)


_task_started: dict[str, float] = {}
_task_spans: dict[str, object] = {}


@task_prerun.connect
def _telemetry_task_started(task_id=None, task=None, **kwargs):
    if not task_id or task is None:
        return
    _task_started[task_id] = perf_counter()
    tracer = get_tracer()
    if tracer is not None:
        span = tracer.start_span(f"celery.{task.name}")
        span.set_attribute("celery.task_name", task.name)
        span.set_attribute("celery.task_id", task_id)
        _task_spans[task_id] = span


def _finish_task(task_id, task_name: str, status: str):
    started = _task_started.pop(task_id, None)
    if started is not None:
        CELERY_TASK_LATENCY.labels(task_name).observe(perf_counter() - started)
    CELERY_TASKS.labels(task_name, status).inc()
    span = _task_spans.pop(task_id, None)
    if span is not None:
        try:
            span.set_attribute("celery.status", status)
            span.end()
        except Exception:
            pass


@task_postrun.connect
def _telemetry_task_finished(task_id=None, task=None, state=None, **kwargs):
    if task_id and task is not None:
        _finish_task(task_id, task.name, "success" if state == "SUCCESS" else str(state or "finished").lower())


@task_failure.connect
def _telemetry_task_failed(task_id=None, task=None, **kwargs):
    if task_id and task is not None:
        _finish_task(task_id, task.name, "failure")

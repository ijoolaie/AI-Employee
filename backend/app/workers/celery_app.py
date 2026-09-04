"""Celery application instance and explicit queue topology.

Workers consume only their assigned queues. Tasks that are not explicitly
routed are sent to ``unrouted`` and no production worker consumes that queue;
this prevents an unknown task from silently landing on an execution worker.
"""

from time import perf_counter

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun
from kombu import Queue

from app.core.config import get_settings
from app.core.metrics import CELERY_TASKS, CELERY_TASK_LATENCY
from app.core.telemetry import get_tracer

settings = get_settings()

celery_app = Celery(
    "aiep",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.run_worker",
        "app.workers.workflow_worker",
        "app.workers.workflow_trigger_worker",
        "app.workers.outbox_worker",
        "app.workers.email_worker",
        "app.workers.test_center_worker",
    ],
)


# Phase 14.3: scheduling policy is an explicit, observable contract. Keep the
# cadence centralized so operations can tune schedules without hunting through
# worker implementations.
SCHEDULE_INTERVALS = {
    "workflow_schedule_tick_seconds": 30.0,
    "workflow_approval_expiry_seconds": 30.0,
    "workflow_timeout_sweep_seconds": 30.0,
    "test_center_expiration_sweep_seconds": 30.0,
    "outbox_dispatch_seconds": 5.0,
}

# Queue names are intentionally stable deployment contracts. ``unrouted`` is
# a safety sink: no worker command consumes it.
EXECUTION_QUEUE = "execution"
TEST_CENTER_QUEUE = "test_center"
CONTROL_QUEUE = "control"
OUTBOX_QUEUE = "outbox"
EMAIL_QUEUE = "email"
UNROUTED_QUEUE = "unrouted"

TASK_ROUTES = {
    "run.execute": {"queue": EXECUTION_QUEUE},
    "workflow.execute": {"queue": EXECUTION_QUEUE},
    "workflow.parallel_branch": {"queue": EXECUTION_QUEUE},
    "test_center.execute_run": {"queue": TEST_CENTER_QUEUE},
    "workflow.schedule_tick": {"queue": CONTROL_QUEUE},
    "workflow.approval_expiry": {"queue": CONTROL_QUEUE},
    "workflow.timeout_sweep": {"queue": CONTROL_QUEUE},
    "workflow.event_dispatch": {"queue": CONTROL_QUEUE},
    "test_center.expiration_sweep": {"queue": CONTROL_QUEUE},
    "outbox.dispatch": {"queue": OUTBOX_QUEUE},
    "email.send": {"queue": EMAIL_QUEUE},
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Phase 14.2: bound broker-side prefetch so one worker cannot reserve an
    # unbounded backlog. Fair dispatch is delegated to the broker instead of
    # allowing a busy process to hoard messages.
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue=UNROUTED_QUEUE,
    task_default_exchange=UNROUTED_QUEUE,
    task_default_routing_key=UNROUTED_QUEUE,
    task_routes=TASK_ROUTES,
    # Hard capacity is a deployment contract. Environment-specific worker
    # concurrency remains explicit in the worker command; tasks never inherit
    # an unbounded prefetch backlog.
    worker_max_tasks_per_child=1000,
    task_queues=(
        Queue(EXECUTION_QUEUE),
        Queue(TEST_CENTER_QUEUE),
        Queue(CONTROL_QUEUE),
        Queue(OUTBOX_QUEUE),
        Queue(EMAIL_QUEUE),
        Queue(UNROUTED_QUEUE),
    ),
    beat_schedule={
        "workflow-schedule-tick": {
            "task": "workflow.schedule_tick",
            "schedule": SCHEDULE_INTERVALS["workflow_schedule_tick_seconds"],
        },
        "workflow-approval-expiry": {
            "task": "workflow.approval_expiry",
            "schedule": SCHEDULE_INTERVALS["workflow_approval_expiry_seconds"],
        },
        "workflow-timeout-sweep": {
            "task": "workflow.timeout_sweep",
            "schedule": SCHEDULE_INTERVALS["workflow_timeout_sweep_seconds"],
        },
        "test-center-expiration-sweep": {
            "task": "test_center.expiration_sweep",
            "schedule": SCHEDULE_INTERVALS["test_center_expiration_sweep_seconds"],
        },
        "outbox-dispatch": {"task": "outbox.dispatch", "schedule": SCHEDULE_INTERVALS["outbox_dispatch_seconds"]},
    },
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
        _finish_task(
            task_id,
            task.name,
            "success" if state == "SUCCESS" else str(state or "finished").lower(),
        )


@task_failure.connect
def _telemetry_task_failed(task_id=None, task=None, **kwargs):
    if task_id and task is not None:
        _finish_task(task_id, task.name, "failure")

from app.services.tenant_fair_scheduler import FairnessDecision
from app.workers.celery_app import (
    CONTROL_QUEUE,
    EMAIL_QUEUE,
    EXECUTION_QUEUE,
    OUTBOX_QUEUE,
    TASK_ROUTES,
    SCHEDULE_INTERVALS,
    TEST_CENTER_QUEUE,
    UNROUTED_QUEUE,
    celery_app,
    tenant_fair_route,
)


def test_all_registered_tasks_have_explicit_isolation_routes():
    expected = {
        "run.execute": EXECUTION_QUEUE,
        "workflow.execute": EXECUTION_QUEUE,
        "workflow.parallel_branch": EXECUTION_QUEUE,
        "test_center.execute_run": TEST_CENTER_QUEUE,
        "workflow.schedule_tick": CONTROL_QUEUE,
        "workflow.approval_expiry": CONTROL_QUEUE,
        "workflow.timeout_sweep": CONTROL_QUEUE,
        "workflow.event_dispatch": CONTROL_QUEUE,
        "test_center.expiration_sweep": CONTROL_QUEUE,
        "outbox.dispatch": OUTBOX_QUEUE,
        "email.send": EMAIL_QUEUE,
    }
    assert {name: route["queue"] for name, route in TASK_ROUTES.items()} == expected


def test_unknown_tasks_use_unrouted_safety_queue():
    assert celery_app.conf.task_default_queue == UNROUTED_QUEUE
    assert UNROUTED_QUEUE not in {
        EXECUTION_QUEUE,
        TEST_CENTER_QUEUE,
        CONTROL_QUEUE,
        OUTBOX_QUEUE,
        EMAIL_QUEUE,
    }


def test_worker_delivery_is_bounded_and_late_acked():
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True


def test_worker_recycling_has_an_explicit_bound():
    assert celery_app.conf.worker_max_tasks_per_child == 1000


def test_scheduling_intervals_are_explicit_positive_contracts():
    assert SCHEDULE_INTERVALS
    assert all(value > 0 for value in SCHEDULE_INTERVALS.values())
    assert SCHEDULE_INTERVALS["outbox_dispatch_seconds"] <= SCHEDULE_INTERVALS["workflow_schedule_tick_seconds"]


def test_fair_router_extracts_tenant_context_and_adds_bounded_priority(monkeypatch):
    class FakeScheduler:
        def route(self, tenant_id):
            assert tenant_id == "tenant-a"
            return FairnessDecision("tenant-a", 3.0, 2, 1.0)

    import app.workers.celery_app as module
    monkeypatch.setattr(module, "_fair_scheduler", FakeScheduler())

    assert tenant_fair_route("run.execute", ("run-1", "tenant-a"), {}, {}, None) == {
        "queue": EXECUTION_QUEUE,
        "priority": 2,
    }


def test_fair_router_does_not_touch_non_tenant_control_tasks():
    assert tenant_fair_route("workflow.schedule_tick", (), {}, {}, None) is None

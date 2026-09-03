# Phase 14.1 — Celery Queue / Worker Isolation

Phase 14.1 defines an explicit queue topology so execution work cannot be
silently consumed by maintenance or side-effect workers.

## Queue contract

| Queue | Tasks | Worker |
|---|---|---|
| `execution` | `run.execute`, `workflow.execute`, `workflow.parallel_branch` | `worker` |
| `test_center` | `test_center.execute_run` | `worker-test-center` |
| `control` | schedule tick, approval expiry, timeout sweep, event dispatch, test-center expiration | `worker-control` |
| `outbox` | `outbox.dispatch` | `worker-outbox` |
| `email` | `email.send` | `worker-email` |
| `unrouted` | unknown/unregistered routing | **no worker** |

The Celery application uses exact `task_routes` entries for every registered
task. The default queue is `unrouted`, which is deliberately not consumed by
any Compose worker. This is a fail-closed routing boundary: adding a new task
requires an explicit route and worker decision rather than inheriting an
execution-capable shared queue.

## Deployment rules

- `worker` consumes only `execution`.
- `worker-test-center` consumes only `test_center`.
- `worker-control` consumes only `control`.
- `worker-outbox` consumes only `outbox`.
- `worker-email` consumes only `email`.
- `beat` is a scheduler only; it does not consume worker queues.
- All workers share the existing broker/result backend and database settings;
  queue separation is enforced at the Celery consumer boundary.

## Verification boundary

Unit coverage asserts the complete task-to-queue map and the `unrouted`
safety default. CI remains the engineering verification gate. This change
does not, by itself, establish external production certification, capacity
limits, SLO compliance, or customer acceptance.

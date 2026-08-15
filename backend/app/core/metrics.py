"""Prometheus metrics for Phase 1 operational observability.

Labels intentionally avoid tenant/user IDs to prevent unbounded cardinality.
Tenant-scoped detail remains available through the authenticated operations
metrics API and the durable Trace/Usage surfaces.
"""
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter("aiep_http_requests_total", "HTTP requests", ["method", "path", "status"])
HTTP_LATENCY = Histogram("aiep_http_request_duration_seconds", "HTTP request latency", ["method", "path"])
WORKFLOW_RUNS = Counter("aiep_workflow_runs_total", "Workflow execution attempts", ["status"])
WORKFLOW_STEPS = Counter("aiep_workflow_steps_total", "Workflow step outcomes", ["step_type", "status"])
WORKFLOW_LATENCY = Histogram("aiep_workflow_duration_seconds", "Workflow execution duration")
AI_CALLS = Counter("aiep_ai_provider_calls_total", "AI provider calls", ["provider", "status"])
AI_LATENCY = Histogram("aiep_ai_provider_latency_seconds", "AI provider latency", ["provider"])
AI_TOKENS = Counter("aiep_ai_tokens_total", "AI tokens consumed", ["provider", "kind"])
AI_COST = Counter("aiep_ai_cost_usd_total", "AI provider cost in USD", ["provider"])
OUTBOX_DISPATCH = Counter("aiep_outbox_dispatch_total", "Outbox dispatch attempts", ["status", "kind"])
OUTBOX_RETRIES = Counter("aiep_outbox_retries_total", "Outbox retries", ["kind"])
OUTBOX_DEAD = Counter("aiep_outbox_dead_total", "Outbox messages moved to DLQ", ["kind"])
OUTBOX_QUEUE = Gauge("aiep_outbox_messages", "Current durable outbox messages", ["status"])
WORKFLOW_RUNS_DB = Gauge("aiep_workflow_runs_db", "Current workflow run rows")
WORKFLOW_STEPS_DB = Gauge("aiep_workflow_steps_db", "Current workflow step rows")
CELERY_TASKS = Counter("aiep_celery_tasks_total", "Celery task executions", ["task", "status"])
CELERY_TASK_LATENCY = Histogram("aiep_celery_task_duration_seconds", "Celery task duration", ["task"])
REDIS_QUEUE_DEPTH = Gauge("aiep_redis_broker_queue_depth", "Redis broker queue depth", ["queue"])
DEPENDENCY_UP = Gauge("aiep_dependency_up", "Dependency health: 1 up, 0 down", ["dependency"])

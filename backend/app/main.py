"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
import os
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, SecurityHardeningMiddleware, SecurityHeadersMiddleware
from app.core.telemetry import init_telemetry
from app.schemas.common import APIErrorResponse, ErrorBody

settings = get_settings()
configure_logging(debug=settings.debug)
init_telemetry()

API_VERSION = "1.0.0-rc.8"
BACKEND_PACKAGE_VERSION = "1.1.1"
FRONTEND_PACKAGE_VERSION = "1.1.1"
PRODUCT_VERSION = os.getenv("PRODUCT_VERSION", "unreleased")
GIT_COMMIT_SHA = os.getenv("GIT_COMMIT_SHA", "unknown")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=API_VERSION,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Inner middlewares first; CORS must be outermost (added last) so every
# response — including rate-limit / early returns — gets CORS headers.
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHardeningMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from app.core.metrics import HTTP_REQUESTS, HTTP_LATENCY
    REQUEST_COUNT = HTTP_REQUESTS
    REQUEST_LATENCY = HTTP_LATENCY
except Exception:
    REQUEST_COUNT = REQUEST_LATENCY = None

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from app.core.database import engine
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
except Exception:
    pass

app.add_exception_handler(AppError, app_error_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Normalize FastAPI HTTPException into the standard API error envelope."""
    detail = exc.detail
    if isinstance(detail, list):
        message = "; ".join(
            str(item.get("msg", item)) if isinstance(item, dict) else str(item)
            for item in detail
        )
    else:
        message = str(detail) if detail else "Request failed"

    code_map = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorResponse(
            success=False,
            error=ErrorBody(code=code, message=message),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=APIErrorResponse(
            success=False,
            error=ErrorBody(
                code="INTERNAL_ERROR",
                message="An internal error occurred",
            ),
        ).model_dump(),
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/metrics")
async def metrics(request: Request):
    """Prometheus scrape endpoint protected by a dedicated bearer token.

    Production must configure METRICS_AUTH_TOKEN. Development may omit the
    token to preserve local observability convenience; production never falls
    back to an unauthenticated metrics surface.
    """
    expected_token = os.getenv("METRICS_AUTH_TOKEN")
    if settings.app_env.lower() in {"production", "prod"} and not expected_token:
        raise HTTPException(status_code=503, detail="Metrics authentication is not configured")
    if expected_token:
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or not secrets.compare_digest(token, expected_token):
            raise HTTPException(status_code=401, detail="Metrics authentication required", headers={"WWW-Authenticate": "Bearer"})

    if REQUEST_COUNT is None:
        return Response(content="", media_type="text/plain")
    try:
        from sqlalchemy import func, select
        from app.core.database import engine
        from app.models.workflow import WorkflowRun, WorkflowStepRun
        from app.models.outbox import OutboxMessage
        from app.core.metrics import OUTBOX_QUEUE, WORKFLOW_RUNS_DB, WORKFLOW_STEPS_DB, REDIS_QUEUE_DEPTH, DEPENDENCY_UP
        from redis.asyncio import Redis
        async with engine.connect() as conn:
            for state in ("pending", "processing", "dead", "dispatched"):
                value = (await conn.execute(select(func.count()).select_from(OutboxMessage).where(OutboxMessage.status == state))).scalar_one()
                OUTBOX_QUEUE.labels(state).set(value)
            WORKFLOW_RUNS_DB.set((await conn.execute(select(func.count()).select_from(WorkflowRun))).scalar_one())
            WORKFLOW_STEPS_DB.set((await conn.execute(select(func.count()).select_from(WorkflowStepRun))).scalar_one())
            DEPENDENCY_UP.labels("postgres").set(1)
    except Exception:
        DEPENDENCY_UP.labels("postgres").set(0)
    try:
        redis_client = Redis.from_url(settings.celery_broker_url, decode_responses=True)
        REDIS_QUEUE_DEPTH.labels("celery").set(await redis_client.llen("celery"))
        DEPENDENCY_UP.labels("redis").set(1)
        await redis_client.aclose()
    except Exception:
        DEPENDENCY_UP.labels("redis").set(0)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": API_VERSION,
        "build": {
            "product_version": PRODUCT_VERSION,
            "backend_package_version": BACKEND_PACKAGE_VERSION,
            "frontend_package_version": FRONTEND_PACKAGE_VERSION,
            "api_version": API_VERSION,
            "git_commit_sha": GIT_COMMIT_SHA,
            "environment": settings.app_env,
        },
    }


@app.get("/health/dependencies")
async def dependency_health():
    """Fail-closed readiness check for PostgreSQL and Redis."""
    from sqlalchemy import text
    from app.core.database import engine
    from redis.asyncio import Redis

    checks = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error:{type(exc).__name__}"

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error:{type(exc).__name__}"
    finally:
        await redis_client.aclose()

    healthy = all(value == "ok" for value in checks.values())
    if not healthy:
        raise HTTPException(status_code=503, detail={"status": "degraded", "checks": checks})
    return {
        "status": "ok",
        "checks": checks,
        "version": API_VERSION,
        "build": {
            "product_version": PRODUCT_VERSION,
            "backend_package_version": BACKEND_PACKAGE_VERSION,
            "frontend_package_version": FRONTEND_PACKAGE_VERSION,
            "api_version": API_VERSION,
            "git_commit_sha": GIT_COMMIT_SHA,
            "environment": settings.app_env,
        },
    }

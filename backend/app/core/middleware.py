"""Request-scoped observability middleware.

Assigns/propagates X-Request-ID, binds it (and tenant/user, once known)
to the logging context vars, and emits one structured access-log line per
request with status + duration. This is the Telemetry baseline described
in docs v1.2 §6 — independent of, and a prerequisite for, the richer
per-Run Trace records in the Employee Framework / AI Core.
"""

from __future__ import annotations

import logging
import time
from ipaddress import ip_address

from redis.asyncio import Redis

from app.core.config import get_settings

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import new_request_id, request_id_var, tenant_id_var, user_id_var

access_logger = logging.getLogger("app.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming_id = request.headers.get("x-request-id")
        req_id = incoming_id or new_request_id()

        req_token = request_id_var.set(req_id)
        tenant_token = tenant_id_var.set(None)
        user_token = user_id_var.set(None)
        request.state.request_id = req_id

        start = time.perf_counter()
        status_code = 500
        span = None
        try:
            try:
                from opentelemetry import trace
                span = trace.get_current_span()
                if span is not None:
                    span.set_attribute("http.request_id", req_id)
            except Exception:
                span = None
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            if span is not None:
                try:
                    span.set_attribute("http.status_code", status_code)
                except Exception:
                    pass
            try:
                from app.core.metrics import HTTP_REQUESTS, HTTP_LATENCY
                HTTP_REQUESTS.labels(request.method, request.url.path, str(status_code)).inc()
                HTTP_LATENCY.labels(request.method, request.url.path).observe(duration_ms / 1000.0)
            except Exception:
                pass
            access_logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            request_id_var.reset(req_token)
            tenant_id_var.reset(tenant_token)
            user_id_var.reset(user_token)

    @staticmethod
    def bind_identity(tenant_id: str | None, user_id: str | None) -> None:
        """Called once auth resolves the caller (see core.deps) so the rest
        of the request's log lines carry tenant/user without re-passing them."""
        if tenant_id is not None:
            tenant_id_var.set(tenant_id)
        if user_id is not None:
            user_id_var.set(user_id)


class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    """Redis-backed rate limiting plus early request-size enforcement.

    The limiter is intentionally path-aware. Public webhook endpoints receive a
    tighter bucket than authenticated application endpoints. If Redis is down,
    the default behavior is fail-open for availability; operators can enable
    fail-closed mode for production.
    """
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.redis = Redis.from_url(self.settings.redis_url, decode_responses=True)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.settings.rate_limit_enabled:
            return await call_next(request)

        # Reject obviously oversized requests before application body parsing.
        limit = self.settings.webhook_max_payload_bytes if request.url.path.startswith('/api/v1/webhooks/') else 5 * 1024 * 1024
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                if int(content_length) > limit:
                    return Response(content='Payload too large', status_code=413, media_type='text/plain')
            except ValueError:
                return Response(content='Invalid Content-Length', status_code=400, media_type='text/plain')

        client = request.client.host if request.client else 'unknown'
        try:
            ip = str(ip_address(client))
        except ValueError:
            ip = client
        is_webhook = request.url.path.startswith('/api/v1/webhooks/')
        max_requests = self.settings.webhook_rate_limit_requests if is_webhook else self.settings.rate_limit_requests
        window = self.settings.webhook_rate_limit_window_seconds if is_webhook else self.settings.rate_limit_window_seconds
        bucket = int(time.time() // window)
        key = f"rl:{'webhook' if is_webhook else 'api'}:{ip}:{bucket}"
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, window + 1)
            if count > max_requests:
                retry_after = window - (int(time.time()) % window)
                return Response(content='Rate limit exceeded', status_code=429, headers={'Retry-After': str(retry_after)}, media_type='text/plain')
        except Exception:
            if self.settings.rate_limit_fail_closed:
                return Response(content='Rate limiter unavailable', status_code=503, media_type='text/plain')
        return await call_next(request)

    async def close(self):
        await self.redis.aclose()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add browser/security headers to every HTTP response.

    API consumers are unaffected; CSP is intentionally not set here because
    the FastAPI service is not the application's HTML renderer.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

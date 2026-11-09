"""Request logging and a small in-process rate limiter.

The limiter is intentionally simple: it protects a single-process deployment from
accidental abuse without adding Redis. For multi-replica deployments, replace the
store with Redis (documented in the deployment guide).
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_settings

logger = logging.getLogger("roleprint.request")
access_logger = logging.getLogger("roleprint.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration = (time.perf_counter() - started) * 1000
            access_logger.exception(
                "request_id=%s method=%s path=%s status=500 duration_ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                duration,
            )
            raise
        duration = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        access_logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    _hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.enable_rate_limit or request.url.path in {"/health", "/docs", "/openapi.json"}:
            return await call_next(request)

        forwarded = request.headers.get("x-forwarded-for", "")
        client = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )
        key = f"{client}:{request.url.path}"
        now = time.monotonic()
        window = settings.rate_limit_window_seconds
        bucket = self._hits[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_requests:
            retry_after = max(1, int(window - (now - bucket[0])))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down and try again shortly.",
                    "error": {"code": "rate_limited", "message": "Too many requests."},
                },
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)
        return await call_next(request)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=False,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

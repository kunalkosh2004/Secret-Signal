"""
Security middleware for Secret Signal.

Provides:
  - Security headers on every HTTP response
  - Request ID injection (propagated through context vars)
  - Request logging (structured)
  - CORS from environment config
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import (
    generate_request_id,
    get_logger,
    request_id_var,
)

logger = get_logger("app.core.security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every HTTP response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # CSP — restrictive but allows inline scripts for React dev
        # In production, tighten this with nonces or hashes
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss: http: https:; "
            "font-src 'self';"
        )

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns a unique request ID to every request and injects it into context."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use incoming X-Request-ID header if present, otherwise generate
        req_id = request.headers.get("X-Request-ID", generate_request_id())
        request_id_var.set(req_id)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Attach request ID to response
        response.headers["X-Request-ID"] = req_id

        # Structured request log
        logger.info(
            "http_request",
            extra={
                "request_id": req_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            },
        )

        return response

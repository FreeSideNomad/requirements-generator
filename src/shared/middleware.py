"""
Custom middleware for the Requirements Generator application.
Handles logging, tenant context, session management, and rate limiting.
"""

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response information."""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Add request ID to context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time=round(process_time, 4),
            )

            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                process_time=round(process_time, 4),
            )
            raise


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for multi-tenant context management."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Extract and validate tenant context from request."""
        tenant_id = None
        tenant_subdomain = None

        # Extract tenant from subdomain (e.g., banking.requirements-generator.com)
        host = request.headers.get("host", "")
        if "." in host and not host.startswith("localhost"):
            tenant_subdomain = host.split(".")[0]

        # Extract tenant from headers (for API calls)
        if not tenant_subdomain:
            tenant_id = request.headers.get("X-Tenant-ID")
            tenant_subdomain = request.headers.get("X-Tenant-Subdomain")

        # Extract tenant from path (fallback)
        if not tenant_subdomain and request.url.path.startswith("/tenant/"):
            path_parts = request.url.path.split("/")
            if len(path_parts) > 2:
                tenant_subdomain = path_parts[2]

        # Add tenant context
        if tenant_id or tenant_subdomain:
            structlog.contextvars.bind_contextvars(
                tenant_id=tenant_id,
                tenant_subdomain=tenant_subdomain,
            )

        # Store in request state for route handlers
        request.state.tenant_id = tenant_id
        request.state.tenant_subdomain = tenant_subdomain

        return await call_next(request)


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for session management and user context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Extract and validate user session from request."""
        session_id = None
        user_id = None

        # Extract session from cookie
        session_id = request.cookies.get("session_id")

        # Extract session from Authorization header
        if not session_id:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This will be validated in auth middleware later
                session_id = auth_header[7:]  # Remove "Bearer " prefix

        # Extract user context (will be populated by auth service)
        user_id = request.headers.get("X-User-ID")

        # Add session context
        if session_id or user_id:
            structlog.contextvars.bind_contextvars(
                session_id=session_id,
                user_id=user_id,
            )

        # Store in request state
        request.state.session_id = session_id
        request.state.user_id = user_id

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for basic rate limiting."""

    def __init__(self, app, calls_per_minute: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or settings.rate_limit_per_minute
        self.requests = {}  # Simple in-memory store (should use Redis in production)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        if settings.is_development:
            # Skip rate limiting in development
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time())
        minute_window = current_time // 60

        # Get request count for this IP and minute window
        key = f"{client_ip}:{minute_window}"
        request_count = self.requests.get(key, 0)

        if request_count >= self.calls_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                request_count=request_count,
                limit=self.calls_per_minute,
            )

            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )

        # Increment counter
        self.requests[key] = request_count + 1

        # Clean old entries (simple cleanup)
        if len(self.requests) > 10000:  # Prevent memory issues
            old_keys = [k for k in self.requests.keys() if int(k.split(":")[1]) < minute_window - 5]
            for old_key in old_keys:
                del self.requests[old_key]

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to all responses."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if not settings.is_development:
            # Add HSTS header in production
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
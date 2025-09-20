"""
Test application factory for tests without external dependencies.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.config import get_settings
from src.shared.database import init_database, close_database
from src.main import register_exception_handlers
from src.shared.middleware import (
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    TenantMiddleware,
    RateLimitMiddleware,
)
from src.shared.routes import health_router


@asynccontextmanager
async def test_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Test application lifespan manager without Redis."""
    settings = get_settings()

    try:
        # Only initialize database for tests
        await init_database()
        yield
    finally:
        await close_database()


def create_test_app() -> FastAPI:
    """Create a test FastAPI application without Redis dependencies."""
    settings = get_settings()

    app = FastAPI(
        title="Requirements Generator (Test)",
        description="AI-powered requirements gathering platform - Test Mode",
        version=settings.version,
        lifespan=test_lifespan,
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url="/redoc" if settings.environment == "development" else None,
    )

    # Add middleware in reverse order (last added is first executed)

    # Security and CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure properly in production
    )

    # Custom middleware
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TenantMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Setup exception handlers
    register_exception_handlers(app)

    # Include routers
    app.include_router(health_router)

    # Add authentication routes for testing
    from src.auth.routes import auth_router
    app.include_router(auth_router, tags=["authentication"])

    return app
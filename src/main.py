"""
FastAPI application entry point for Requirements Generator.
Multi-tenant SaaS platform with AI-powered requirements gathering.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import settings
from src.shared.exceptions import AppException
from src.shared.middleware import (
    LoggingMiddleware,
    TenantMiddleware,
    SessionMiddleware,
    RateLimitMiddleware,
)
from src.shared.database import init_database, close_database
from src.shared.redis_client import init_redis, close_redis

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.is_development else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        min_level=getattr(logging, settings.log_level.upper())
    ),
    logger_factory=structlog.WriteLoggerFactory(sys.stdout),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup and shutdown events."""
    logger.info("Starting Requirements Generator application", version=settings.version)

    # Startup
    try:
        await init_database()
        await init_redis()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise

    yield  # Application is running

    # Shutdown
    try:
        await close_database()
        await close_redis()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error("Error during application shutdown", error=str(e))


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="AI-powered requirements gathering platform using FastAPI + Pydantic",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        openapi_url="/api/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Configure CORS
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=settings.cors_credentials,
            allow_methods=settings.cors_methods,
            allow_headers=settings.cors_headers,
        )

    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.is_development else ["localhost", "127.0.0.1"],
    )

    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TenantMiddleware)
    app.add_middleware(SessionMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Configure monitoring
    if settings.enable_metrics:
        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app, endpoint="/metrics")

    # Register routes
    register_routes(app)

    # Exception handlers
    register_exception_handlers(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register all application routes."""
    from src.shared.routes import health_router
    from src.auth.routes import auth_router
    from src.tenants.routes import tenants_router
    from src.web.routes import web_router

    # Core routes
    app.include_router(health_router, tags=["health"])
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(tenants_router, prefix="/api/tenants", tags=["tenants"])

    # Web interface routes
    app.include_router(web_router, tags=["web"])

    # Feature routes
    from src.ai.routes import router as ai_router
    from src.requirements.routes import router as requirements_router
    # from src.domain.routes import domain_router

    app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
    app.include_router(requirements_router, prefix="/api/requirements", tags=["requirements"])
    # app.include_router(domain_router, prefix="/api/domain", tags=["domain"])


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.error(
            "Application exception occurred",
            error=exc.message,
            error_code=exc.error_code,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        # Convert validation errors to JSON-serializable format
        errors = []
        for error in exc.errors():
            error_dict = {
                "type": error.get("type"),
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "input": error.get("input"),
            }
            # Handle non-serializable context
            if "ctx" in error:
                ctx = error["ctx"]
                if isinstance(ctx, dict):
                    error_dict["ctx"] = {
                        k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                        for k, v in ctx.items()
                    }
            errors.append(error_dict)

        logger.warning(
            "Validation error occurred",
            errors=errors,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": errors,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(
            "Unexpected exception occurred",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
        )

        if settings.is_development:
            import traceback
            details = traceback.format_exc()
        else:
            details = None

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": details,
                }
            },
        )


# Create the FastAPI application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        workers=1 if settings.reload else settings.workers,
    )
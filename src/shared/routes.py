"""
Shared API routes for health checks and system information.
"""

from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from src.config import settings
from src.shared.database import get_db_session, engine
from src.shared.redis_client import get_redis_client
from src.shared.models import HealthCheck

logger = structlog.get_logger(__name__)

health_router = APIRouter()


@health_router.get("/health", response_model=HealthCheck)
async def health_check(
    db_session=Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> HealthCheck:
    """
    Comprehensive health check endpoint.
    Checks database, Redis, and other critical services.
    """
    services = {}
    overall_status = "healthy"

    # Check database
    try:
        # Simple database query
        result = await db_session.execute("SELECT 1 as health_check")
        if result.scalar() == 1:
            services["database"] = "healthy"
        else:
            services["database"] = "unhealthy"
            overall_status = "degraded"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        services["database"] = "unhealthy"
        overall_status = "unhealthy"

    # Check Redis
    try:
        await redis_client.ping()
        services["redis"] = "healthy"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        services["redis"] = "unhealthy"
        overall_status = "degraded"

    # Check external services (placeholder)
    services["openai"] = "not_checked"  # Will implement in AI integration stage

    # Additional system information
    details = {
        "environment": settings.environment,
        "debug_mode": settings.debug,
        "uptime": "N/A",  # Can add actual uptime tracking
        "memory_usage": "N/A",  # Can add memory monitoring
    } if settings.is_development else None

    return HealthCheck(
        status=overall_status,
        version=settings.version,
        services=services,
        details=details,
    )


@health_router.get("/health/live")
async def liveness_probe() -> Dict[str, Any]:
    """
    Simple liveness probe for Kubernetes.
    Returns 200 if application is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@health_router.get("/health/ready")
async def readiness_probe(
    db_session=Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes.
    Returns 200 only if all critical services are available.
    """
    try:
        # Check database
        await db_session.execute("SELECT 1")

        # Check Redis
        await redis_client.ping()

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )


@health_router.get("/version")
async def version_info() -> Dict[str, Any]:
    """Get application version and build information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "python_version": "3.11+",
        "framework": "FastAPI",
        "database": "PostgreSQL with asyncpg",
        "cache": "Redis",
        "timestamp": datetime.utcnow().isoformat(),
    }


@health_router.get("/metrics/basic")
async def basic_metrics() -> Dict[str, Any]:
    """
    Basic application metrics.
    More detailed metrics available at /metrics (Prometheus format).
    """
    if not settings.enable_metrics:
        raise HTTPException(
            status_code=404,
            detail="Metrics not enabled"
        )

    # Basic metrics (can be expanded)
    return {
        "requests_total": "N/A",  # Will implement with proper metrics
        "active_sessions": "N/A",
        "database_connections": "N/A",
        "memory_usage": "N/A",
        "uptime_seconds": "N/A",
        "timestamp": datetime.utcnow().isoformat(),
    }
"""
Database configuration and connection management.
Provides async SQLAlchemy setup with connection pooling.
"""

import asyncio
from typing import AsyncGenerator, Optional

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from sqlalchemy import MetaData

from src.config import settings

logger = structlog.get_logger(__name__)

# Global engine and session maker
engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


async def init_database() -> None:
    """Initialize database connection and engine."""
    global engine, async_session_maker

    logger.info("Initializing database connection", url=settings.database_url.split("@")[0] + "@***")

    try:
        # Create async engine with appropriate pool for database type
        engine_kwargs = {
            "echo": settings.database_echo,
            "pool_pre_ping": True,
        }

        # Configure pooling based on database type and environment
        if "sqlite" in settings.database_url:
            # SQLite with async requires StaticPool or NullPool
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            })
        elif settings.is_testing:
            # Use NullPool for testing to avoid connection sharing issues
            engine_kwargs["poolclass"] = NullPool
        else:
            # Use QueuePool for PostgreSQL and other databases
            engine_kwargs.update({
                "poolclass": QueuePool,
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_recycle": 3600,  # Recycle connections every hour
            })

        engine = create_async_engine(settings.database_url, **engine_kwargs)

        # Create session maker
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        # Test connection
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Database connection initialized successfully")

    except Exception as e:
        logger.error("Failed to initialize database connection", error=str(e))
        raise


async def close_database() -> None:
    """Close database connections."""
    global engine

    if engine:
        logger.info("Closing database connections")
        await engine.dispose()
        logger.info("Database connections closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Use this in FastAPI route dependencies.
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_database_tables() -> None:
    """Create all database tables. Used for testing and initial setup."""
    if not engine:
        raise RuntimeError("Database engine not initialized")

    logger.info("Creating database tables")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


async def drop_database_tables() -> None:
    """Drop all database tables. Used for testing cleanup."""
    if not engine:
        raise RuntimeError("Database engine not initialized")

    logger.info("Dropping database tables")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise


class DatabaseSession:
    """Context manager for database sessions with transaction handling."""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        """Enter async context manager."""
        if not async_session_maker:
            raise RuntimeError("Database not initialized")

        self.session = async_session_maker()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager with proper cleanup."""
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()


async def execute_with_retry(operation, max_retries: int = 3, delay: float = 1.0):
    """
    Execute database operation with retry logic.
    Useful for handling temporary connection issues.
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    "Database operation failed, retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                logger.error(
                    "Database operation failed after all retries",
                    attempts=max_retries,
                    error=str(e),
                )

    raise last_exception


# Import all models for Alembic to discover them
from src.tenants.models import Tenant, TenantInvitation, TenantFeature  # noqa: E402
from src.auth.models import User, UserSession, UserInvitation, AuditLog  # noqa: E402
from src.projects.models import Project, ProjectMember, Requirement, RequirementComment  # noqa: E402
"""
Global test configuration and fixtures.
Provides shared test utilities and database setup.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.shared.database import Base, get_db_session
from src.config import get_settings
from tests.test_app import create_test_app


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def test_client(test_db_session: AsyncSession) -> TestClient:
    """Create a test client with overridden database dependency."""

    async def override_get_db_session():
        yield test_db_session

    app = create_test_app()
    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as client:
        yield client

    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Get test-specific settings."""
    settings = get_settings()
    settings.environment = "testing"
    settings.database_url = TEST_DATABASE_URL
    return settings


# Test data factories
@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for testing."""
    return {
        "name": "Test Tenant",
        "subdomain": "test-tenant",
        "industry": "banking",
        "subscription_tier": "professional",
        "features": {
            "ai_assistance": True,
            "advanced_templates": True,
            "api_access": False
        },
        "settings": {
            "theme": "banking",
            "notifications": True
        }
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "contributor",
        "is_active": True,
        "is_verified": True
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for requirements gathering",
        "key": "TEST-001",
        "project_type": "feature",
        "priority": "high",
        "objectives": [
            "Implement user authentication",
            "Create project dashboard",
            "Add reporting features"
        ],
        "success_criteria": [
            "User can login successfully",
            "Dashboard loads within 2 seconds",
            "Reports are generated accurately"
        ]
    }


@pytest.fixture
def sample_requirement_data():
    """Sample requirement data for testing."""
    return {
        "title": "User Authentication",
        "description": "Users should be able to log in with email and password",
        "key": "REQ-001",
        "requirement_type": "functional",
        "priority": "high",
        "acceptance_criteria": [
            "User enters valid email and password",
            "System validates credentials",
            "User is redirected to dashboard on success",
            "Error message shown on invalid credentials"
        ],
        "business_rules": [
            "Password must be at least 8 characters",
            "Account locked after 5 failed attempts",
            "Session expires after 24 hours"
        ]
    }


# Helper functions for tests
class TestHelper:
    """Test utility functions."""

    @staticmethod
    async def create_test_tenant(session: AsyncSession, **kwargs):
        """Create a test tenant."""
        from src.tenants.models import Tenant

        tenant_data = {
            "name": "Test Tenant",
            "subdomain": "test",
            "industry": "banking"
        }
        tenant_data.update(kwargs)

        tenant = Tenant(**tenant_data)
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        return tenant

    @staticmethod
    async def create_test_user(session: AsyncSession, tenant_id, **kwargs):
        """Create a test user."""
        from src.auth.models import User

        user_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "tenant_id": tenant_id,
            "role": "contributor"
        }
        user_data.update(kwargs)

        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def create_test_project(session: AsyncSession, tenant_id, owner_id, **kwargs):
        """Create a test project."""
        from src.projects.models import Project

        project_data = {
            "name": "Test Project",
            "key": "TEST-001",
            "tenant_id": tenant_id,
            "owner_id": owner_id
        }
        project_data.update(kwargs)

        project = Project(**project_data)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project


@pytest.fixture
def test_helper():
    """Provide test helper instance."""
    return TestHelper
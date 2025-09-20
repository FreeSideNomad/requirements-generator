"""
Database seeding for development and testing.
Creates test users and tenants for E2E testing.
"""

import asyncio
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.shared.database import get_db_session
from src.auth.models import User, UserRole, UserStatus, AuthProvider
from src.tenants.models import Tenant
from src.auth.jwt_handler import JWTHandler


async def seed_test_data():
    """Seed the database with test data for E2E testing."""
    try:
        async for session in get_db_session():
            await create_test_tenant_and_user(session)
            print("✅ Test data seeded successfully")
            break
    except Exception as e:
        print(f"❌ Failed to seed test data: {e}")


async def create_test_tenant_and_user(session: AsyncSession):
    """Create test tenant and user if they don't exist."""

    # Check if test tenant already exists
    result = await session.execute(
        select(Tenant).where(Tenant.subdomain == "test-tenant")
    )
    test_tenant = result.scalar_one_or_none()

    if not test_tenant:
        # Create test tenant
        test_tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Tenant",
            subdomain="test-tenant",
            industry="banking",
            subscription_tier="professional",
            is_active=True,
            features={
                "ai_assistance": True,
                "advanced_templates": True,
                "api_access": False
            },
            settings={
                "theme": "banking",
                "notifications": True
            }
        )
        session.add(test_tenant)
        await session.flush()  # Get the ID
        print(f"✅ Created test tenant: {test_tenant.name}")

    # Create test users with hashed password
    jwt_handler = JWTHandler()
    password_hash = jwt_handler.hash_password("password123")

    # Check if test user already exists
    result = await session.execute(
        select(User).where(User.email == "test@example.com")
    )
    test_user = result.scalar_one_or_none()

    if not test_user:
        test_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash=password_hash,
            auth_provider=AuthProvider.LOCAL,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_verified=True,
            tenant_id=test_tenant.id,
            role=UserRole.CONTRIBUTOR,
            permissions={}
        )
        session.add(test_user)
        print(f"✅ Created test user: {test_user.email}")

    # Check if admin user already exists
    result = await session.execute(
        select(User).where(User.email == "admin@example.com")
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password_hash=password_hash,
            auth_provider=AuthProvider.LOCAL,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_verified=True,
            tenant_id=test_tenant.id,
            role=UserRole.TENANT_ADMIN,
            permissions={}
        )
        session.add(admin_user)
        print(f"✅ Created admin user: {admin_user.email}")

    # Commit the changes
    await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_test_data())
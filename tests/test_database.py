"""
Test database models and relationships.
Verifies that the domain models work correctly.
"""
import pytest
import uuid
from datetime import datetime, timedelta

from src.tenants.models import Tenant, TenantFeature, Industry, SubscriptionTier
from src.auth.models import User, UserRole, UserSession
from src.projects.models import Project, Requirement, ProjectMember


class TestTenantModels:
    """Test tenant-related models."""

    @pytest.mark.asyncio
    async def test_create_tenant(self, test_db_session, sample_tenant_data):
        """Test creating a tenant."""
        tenant = Tenant(
            name=sample_tenant_data["name"],
            subdomain=sample_tenant_data["subdomain"],
            industry=Industry.BANKING,
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            features=sample_tenant_data["features"],
            settings=sample_tenant_data["settings"]
        )

        test_db_session.add(tenant)
        await test_db_session.commit()
        await test_db_session.refresh(tenant)

        assert tenant.id is not None
        assert tenant.name == sample_tenant_data["name"]
        assert tenant.subdomain == sample_tenant_data["subdomain"]
        assert tenant.industry == Industry.BANKING
        assert tenant.subscription_tier == SubscriptionTier.PROFESSIONAL
        assert tenant.has_feature("ai_assistance") is True
        assert tenant.has_feature("nonexistent_feature") is False

    @pytest.mark.asyncio
    async def test_tenant_feature_management(self, test_db_session):
        """Test tenant feature flag management."""
        # Create tenant
        tenant = Tenant(
            name="Feature Test Tenant",
            subdomain="feature-test",
            industry=Industry.FINTECH
        )
        test_db_session.add(tenant)
        await test_db_session.commit()
        await test_db_session.refresh(tenant)

        # Create feature
        feature = TenantFeature(
            tenant_id=tenant.id,
            feature_name="advanced_ai",
            is_enabled=True,
            usage_limit=100,
            usage_count=50
        )
        test_db_session.add(feature)
        await test_db_session.commit()

        assert feature.is_available is True

        # Test usage increment
        feature.increment_usage()
        assert feature.usage_count == 51

        # Test usage limit
        feature.usage_count = 100
        assert feature.is_available is False

    @pytest.mark.asyncio
    async def test_tenant_properties(self, test_db_session):
        """Test tenant property methods."""
        # Create trial tenant
        tenant = Tenant(
            name="Trial Tenant",
            subdomain="trial",
            industry=Industry.HEALTHCARE,
            status="trial",
            trial_ends_at=datetime.utcnow() + timedelta(days=7)
        )
        test_db_session.add(tenant)
        await test_db_session.commit()

        assert tenant.is_trial_expired is False
        assert tenant.display_name == "Trial Tenant"

        # Test setting retrieval
        tenant.settings = {"theme": "healthcare", "notifications": True}
        assert tenant.get_setting("theme") == "healthcare"
        assert tenant.get_setting("nonexistent", "default") == "default"


class TestUserModels:
    """Test user-related models."""

    @pytest.mark.asyncio
    async def test_create_user(self, test_db_session, test_helper):
        """Test creating a user with tenant relationship."""
        # First create a tenant
        tenant = await test_helper.create_test_tenant(test_db_session)

        # Create user
        user = User(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            tenant_id=tenant.id,
            role=UserRole.CONTRIBUTOR,
            is_active=True,
            is_verified=True
        )

        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        assert user.id is not None
        assert user.email == "testuser@example.com"
        assert user.full_name == "Test User"
        assert user.tenant_id == tenant.id
        assert user.role == UserRole.CONTRIBUTOR

    @pytest.mark.asyncio
    async def test_user_permissions(self, test_db_session, test_helper):
        """Test user permission and role checking."""
        tenant = await test_helper.create_test_tenant(test_db_session)

        # Create admin user
        admin_user = User(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            tenant_id=tenant.id,
            role=UserRole.TENANT_ADMIN,
            permissions={"manage_users": True, "manage_projects": True}
        )

        # Create regular user
        regular_user = User(
            email="user@example.com",
            first_name="Regular",
            last_name="User",
            tenant_id=tenant.id,
            role=UserRole.CONTRIBUTOR,
            permissions={"create_requirements": True}
        )

        test_db_session.add_all([admin_user, regular_user])
        await test_db_session.commit()

        # Test role hierarchy
        assert admin_user.has_role_level(UserRole.CONTRIBUTOR) is True
        assert admin_user.has_role_level(UserRole.TENANT_ADMIN) is True
        assert regular_user.has_role_level(UserRole.TENANT_ADMIN) is False
        assert regular_user.has_role_level(UserRole.CONTRIBUTOR) is True

        # Test permissions
        assert admin_user.has_permission("manage_users") is True
        assert regular_user.has_permission("manage_users") is False
        assert regular_user.has_permission("create_requirements") is True

    @pytest.mark.asyncio
    async def test_user_session(self, test_db_session, test_helper):
        """Test user session management."""
        tenant = await test_helper.create_test_tenant(test_db_session)
        user = await test_helper.create_test_user(test_db_session, tenant.id)

        # Create session
        session = UserSession(
            user_id=user.id,
            session_token="test_token_123",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )

        test_db_session.add(session)
        await test_db_session.commit()

        assert session.is_expired is False

        # Test session extension
        old_expiry = session.expires_at
        session.extend_session(48)
        assert session.expires_at > old_expiry


class TestProjectModels:
    """Test project-related models."""

    @pytest.mark.asyncio
    async def test_create_project(self, test_db_session, test_helper):
        """Test creating a project with relationships."""
        tenant = await test_helper.create_test_tenant(test_db_session)
        user = await test_helper.create_test_user(test_db_session, tenant.id)

        project = Project(
            name="Test Requirements Project",
            description="A project for testing requirements gathering",
            key="TRP-001",
            tenant_id=tenant.id,
            owner_id=user.id,
            project_type="feature",
            priority="high",
            objectives=["Build great software", "Deliver on time"],
            success_criteria=["All tests pass", "User acceptance complete"]
        )

        test_db_session.add(project)
        await test_db_session.commit()
        await test_db_session.refresh(project)

        assert project.id is not None
        assert project.name == "Test Requirements Project"
        assert project.key == "TRP-001"
        assert project.display_name == "[TRP-001] Test Requirements Project"
        assert project.is_active is False  # Default status is draft

    @pytest.mark.asyncio
    async def test_project_members(self, test_db_session, test_helper):
        """Test project team membership."""
        tenant = await test_helper.create_test_tenant(test_db_session)
        owner = await test_helper.create_test_user(test_db_session, tenant.id, email="owner@example.com")
        contributor = await test_helper.create_test_user(test_db_session, tenant.id, email="contributor@example.com")

        project = await test_helper.create_test_project(test_db_session, tenant.id, owner.id)

        # Add project member
        member = ProjectMember(
            project_id=project.id,
            user_id=contributor.id,
            role="contributor",
            permissions={"create_requirements": True, "comment": True}
        )

        test_db_session.add(member)
        await test_db_session.commit()

        assert member.project_id == project.id
        assert member.user_id == contributor.id
        assert member.role == "contributor"
        assert member.is_active is True

    @pytest.mark.asyncio
    async def test_requirements(self, test_db_session, test_helper):
        """Test requirement creation and management."""
        tenant = await test_helper.create_test_tenant(test_db_session)
        user = await test_helper.create_test_user(test_db_session, tenant.id)
        project = await test_helper.create_test_project(test_db_session, tenant.id, user.id)

        requirement = Requirement(
            title="User Login Functionality",
            description="Users must be able to authenticate with email and password",
            key="REQ-001",
            project_id=project.id,
            author_id=user.id,
            requirement_type="functional",
            priority="high",
            acceptance_criteria=[
                "User enters valid credentials",
                "System validates and creates session",
                "User is redirected to dashboard"
            ],
            business_rules=[
                "Password must be at least 8 characters",
                "Account locks after 5 failed attempts"
            ]
        )

        test_db_session.add(requirement)
        await test_db_session.commit()
        await test_db_session.refresh(requirement)

        assert requirement.id is not None
        assert requirement.title == "User Login Functionality"
        assert requirement.key == "REQ-001"
        assert requirement.display_name == "[REQ-001] User Login Functionality"
        assert requirement.project_id == project.id
        assert requirement.author_id == user.id
        assert len(requirement.acceptance_criteria) == 3
        assert len(requirement.business_rules) == 2

    @pytest.mark.asyncio
    async def test_project_progress_tracking(self, test_db_session, test_helper):
        """Test project progress calculation."""
        tenant = await test_helper.create_test_tenant(test_db_session)
        user = await test_helper.create_test_user(test_db_session, tenant.id)
        project = await test_helper.create_test_project(test_db_session, tenant.id, user.id)

        # Create requirements
        req1 = Requirement(
            title="Requirement 1",
            description="First requirement",
            key="REQ-001",
            project_id=project.id,
            author_id=user.id,
            is_approved=True
        )

        req2 = Requirement(
            title="Requirement 2",
            description="Second requirement",
            key="REQ-002",
            project_id=project.id,
            author_id=user.id,
            is_approved=False
        )

        test_db_session.add_all([req1, req2])
        await test_db_session.commit()

        # Update project counts manually (would be done by service layer)
        project.requirements_count = 2
        project.approved_requirements_count = 1
        project.update_progress()

        assert project.completion_percentage == 50
"""
Unit tests for the AuthService class.
Tests user registration, authentication, password management, and invitation flows.
"""

import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from src.auth.service import AuthService
from src.auth.schemas import RegisterRequest, LoginRequest, ChangePasswordRequest, UserInvitationRequest
from src.auth.models import UserRole, UserStatus, AuthProvider
from src.shared.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError


class TestAuthServiceRegistration:
    """Test user registration functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service with mocked dependencies."""
        with patch('src.auth.service.UserRepository') as mock_repo, \
             patch('src.auth.service.RedisClient') as mock_redis:
            service = AuthService()
            service.user_repo = mock_repo.return_value
            service.redis_client = mock_redis.return_value
            return service

    @pytest.fixture
    def registration_data(self):
        """Sample registration data."""
        return RegisterRequest(
            email="test@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            first_name="Test",
            last_name="User",
            username="testuser"
        )

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, registration_data):
        """Test successful user registration."""
        # Setup mocks
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_user = Mock(
            id=user_id,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.TENANT_ADMIN,
            status=UserStatus.PENDING,
            auth_provider=AuthProvider.LOCAL,
            is_active=True,
            is_verified=True,
            tenant_id=tenant_id,
            avatar_url=None,
            timezone="UTC",
            locale="en",
            last_login_at=None,
            permissions={},
            created_at=None,
            updated_at=None
        )

        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=None)
        auth_service.user_repo.create_user = AsyncMock(return_value=mock_user)

        with patch('src.auth.service.jwt_handler.hash_password') as mock_hash:
            mock_hash.return_value = "hashed_password"

            # Execute
            result = await auth_service.register_user(registration_data)

            # Verify
            assert result.email == "test@example.com"
            assert result.first_name == "Test"
            assert result.role == UserRole.TENANT_ADMIN
            auth_service.user_repo.get_user_by_email.assert_called_once_with("test@example.com")
            auth_service.user_repo.create_user.assert_called_once()
            mock_hash.assert_called_once_with("TestPassword123!")

    @pytest.mark.asyncio
    async def test_register_user_email_conflict(self, auth_service, registration_data):
        """Test registration with existing email."""
        # Setup mock to return existing user
        existing_user = Mock(email="test@example.com")
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=existing_user)

        # Execute and verify exception
        with pytest.raises(ConflictError) as exc_info:
            await auth_service.register_user(registration_data)

        assert "already exists" in str(exc_info.value)
        auth_service.user_repo.create_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_user_with_invitation(self, auth_service, registration_data):
        """Test registration with invitation token."""
        # Setup
        tenant_id = uuid.uuid4()
        registration_data.invitation_token = "test_token"

        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=None)
        auth_service.user_repo.create_user = AsyncMock(return_value=Mock(
            id=uuid.uuid4(),
            email="test@example.com",
            role=UserRole.CONTRIBUTOR,
            tenant_id=tenant_id
        ))

        with patch('src.auth.service.jwt_handler.verify_invitation_token') as mock_verify, \
             patch('src.auth.service.jwt_handler.hash_password') as mock_hash:
            mock_verify.return_value = {
                "email": "test@example.com",
                "tenant_id": str(tenant_id),
                "role": "contributor"
            }
            mock_hash.return_value = "hashed_password"

            # Execute
            result = await auth_service.register_user(registration_data, tenant_id)

            # Verify invitation was processed
            mock_verify.assert_called_once_with("test_token")
            auth_service.user_repo.create_user.assert_called_once()


class TestAuthServiceAuthentication:
    """Test user authentication functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service with mocked dependencies."""
        with patch('src.auth.service.UserRepository') as mock_repo, \
             patch('src.auth.service.RedisClient') as mock_redis:
            service = AuthService()
            service.user_repo = mock_repo.return_value
            service.redis_client = mock_redis.return_value
            return service

    @pytest.fixture
    def login_data(self):
        """Sample login data."""
        return LoginRequest(
            email="test@example.com",
            password="TestPassword123!",
            remember_me=True
        )

    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        return Mock(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            is_active=True,
            status=UserStatus.ACTIVE,
            role=UserRole.CONTRIBUTOR,
            tenant_id=uuid.uuid4(),
            permissions=["read", "write"]
        )

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, login_data, mock_user):
        """Test successful user authentication."""
        # Setup mocks
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.user_repo.update_last_login = AsyncMock()
        auth_service._create_session = AsyncMock()

        with patch('src.auth.service.jwt_handler.verify_password') as mock_verify, \
             patch('src.auth.service.jwt_handler.create_access_token') as mock_access, \
             patch('src.auth.service.jwt_handler.create_refresh_token') as mock_refresh:

            mock_verify.return_value = True
            mock_access.return_value = "access_token"
            mock_refresh.return_value = "refresh_token"

            # Execute
            result = await auth_service.authenticate_user(login_data)

            # Verify
            assert result.success is True
            assert result.access_token == "access_token"
            assert result.refresh_token == "refresh_token"
            assert result.user.email == "test@example.com"

            auth_service.user_repo.get_user_by_email.assert_called_once_with("test@example.com")
            mock_verify.assert_called_once_with("TestPassword123!", "hashed_password")
            auth_service.user_repo.update_last_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, login_data):
        """Test authentication with non-existent user."""
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=None)

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.authenticate_user(login_data)

        assert "Invalid email or password" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, login_data, mock_user):
        """Test authentication with wrong password."""
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('src.auth.service.jwt_handler.verify_password') as mock_verify:
            mock_verify.return_value = False

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.authenticate_user(login_data)

            assert "Invalid email or password" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, login_data, mock_user):
        """Test authentication with inactive user."""
        mock_user.is_active = False
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=mock_user)

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.authenticate_user(login_data)

        assert "deactivated" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_user_suspended(self, auth_service, login_data, mock_user):
        """Test authentication with suspended user."""
        mock_user.status = UserStatus.SUSPENDED
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('src.auth.service.jwt_handler.verify_password') as mock_verify:
            mock_verify.return_value = True

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.authenticate_user(login_data)

            assert "suspended" in str(exc_info.value)


class TestAuthServicePasswordManagement:
    """Test password management functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service with mocked dependencies."""
        with patch('src.auth.service.UserRepository') as mock_repo, \
             patch('src.auth.service.RedisClient') as mock_redis:
            service = AuthService()
            service.user_repo = mock_repo.return_value
            service.redis_client = mock_redis.return_value
            return service

    @pytest.fixture
    def password_change_data(self):
        """Sample password change data."""
        return ChangePasswordRequest(
            current_password="OldPassword123!",
            new_password="NewPassword123!"
        )

    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        return Mock(
            id=uuid.uuid4(),
            password_hash="old_hashed_password"
        )

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, password_change_data, mock_user):
        """Test successful password change."""
        user_id = mock_user.id

        # Setup mocks
        auth_service.user_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        auth_service.user_repo.update_password = AsyncMock()
        auth_service._invalidate_all_user_sessions = AsyncMock()

        with patch('src.auth.service.jwt_handler.verify_password') as mock_verify, \
             patch('src.auth.service.jwt_handler.hash_password') as mock_hash:

            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"

            # Execute
            result = await auth_service.change_password(user_id, password_change_data)

            # Verify
            assert result is True
            auth_service.user_repo.get_user_by_id.assert_called_once_with(user_id)
            mock_verify.assert_called_once_with("OldPassword123!", "old_hashed_password")
            mock_hash.assert_called_once_with("NewPassword123!")
            auth_service.user_repo.update_password.assert_called_once_with(user_id, "new_hashed_password")
            auth_service._invalidate_all_user_sessions.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, auth_service, password_change_data):
        """Test password change for non-existent user."""
        user_id = uuid.uuid4()
        auth_service.user_repo.get_user_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await auth_service.change_password(user_id, password_change_data)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service, password_change_data, mock_user):
        """Test password change with wrong current password."""
        user_id = mock_user.id
        auth_service.user_repo.get_user_by_id = AsyncMock(return_value=mock_user)

        with patch('src.auth.service.jwt_handler.verify_password') as mock_verify:
            mock_verify.return_value = False

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.change_password(user_id, password_change_data)

            assert "Current password is incorrect" in str(exc_info.value)


class TestAuthServiceInvitations:
    """Test user invitation functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service with mocked dependencies."""
        with patch('src.auth.service.UserRepository') as mock_repo, \
             patch('src.auth.service.RedisClient') as mock_redis:
            service = AuthService()
            service.user_repo = mock_repo.return_value
            service.redis_client = mock_redis.return_value
            return service

    @pytest.fixture
    def invitation_data(self):
        """Sample invitation data."""
        return UserInvitationRequest(
            email="newuser@example.com",
            role=UserRole.CONTRIBUTOR,
            message="Welcome to our team!"
        )

    @pytest.mark.asyncio
    async def test_invite_user_success(self, auth_service, invitation_data):
        """Test successful user invitation."""
        inviter_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        # Setup mocks
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=None)
        auth_service.user_repo.create_invitation = AsyncMock(return_value=Mock(
            id=uuid.uuid4(),
            expires_at=datetime.utcnow() + timedelta(days=7)
        ))

        with patch('src.auth.service.jwt_handler.generate_invitation_token') as mock_generate:
            mock_generate.return_value = "invitation_token"

            # Execute
            result = await auth_service.invite_user(inviter_id, tenant_id, invitation_data)

            # Verify
            assert result["email"] == "newuser@example.com"
            assert result["role"] == UserRole.CONTRIBUTOR
            assert "invitation_url" in result
            assert "token" in result

            auth_service.user_repo.get_user_by_email.assert_called_once_with("newuser@example.com")
            mock_generate.assert_called_once()
            auth_service.user_repo.create_invitation.assert_called_once()

    @pytest.mark.asyncio
    async def test_invite_existing_user(self, auth_service, invitation_data):
        """Test invitation for existing user."""
        inviter_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        # Setup mock to return existing user
        existing_user = Mock(email="newuser@example.com")
        auth_service.user_repo.get_user_by_email = AsyncMock(return_value=existing_user)

        with pytest.raises(ConflictError) as exc_info:
            await auth_service.invite_user(inviter_id, tenant_id, invitation_data)

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_invitation_success(self, auth_service):
        """Test successful invitation verification."""
        token = "valid_token"

        # Setup mocks
        auth_service.user_repo.get_invitation_by_token = AsyncMock(return_value=Mock(
            is_valid=True
        ))

        with patch('src.auth.service.jwt_handler.verify_invitation_token') as mock_verify:
            mock_verify.return_value = {
                "email": "test@example.com",
                "tenant_id": str(uuid.uuid4()),
                "role": "contributor"
            }

            # Execute
            result = await auth_service.verify_invitation(token)

            # Verify
            assert result["email"] == "test@example.com"
            assert "tenant_id" in result
            mock_verify.assert_called_once_with(token)

    @pytest.mark.asyncio
    async def test_verify_invitation_invalid(self, auth_service):
        """Test verification of invalid invitation."""
        token = "invalid_token"

        auth_service.user_repo.get_invitation_by_token = AsyncMock(return_value=Mock(
            is_valid=False
        ))

        with patch('src.auth.service.jwt_handler.verify_invitation_token') as mock_verify:
            mock_verify.return_value = {"email": "test@example.com"}

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.verify_invitation(token)

            assert "Invalid or expired invitation" in str(exc_info.value)


class TestAuthServiceTenantManagement:
    """Test tenant-related functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service with mocked dependencies."""
        with patch('src.auth.service.UserRepository') as mock_repo, \
             patch('src.auth.service.RedisClient') as mock_redis:
            service = AuthService()
            service.user_repo = mock_repo.return_value
            service.redis_client = mock_redis.return_value
            return service

    @pytest.mark.asyncio
    async def test_user_needs_tenant_no_user(self, auth_service):
        """Test tenant check for non-existent user."""
        user_id = uuid.uuid4()
        auth_service.user_repo.get_user_by_id = AsyncMock(return_value=None)

        result = await auth_service.user_needs_tenant(user_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_user_needs_tenant_no_tenant(self, auth_service):
        """Test tenant check for user with no valid tenant."""
        user_id = uuid.uuid4()
        mock_user = Mock(
            tenant_id=uuid.uuid4(),
            status=UserStatus.PENDING
        )
        auth_service.user_repo.get_user_by_id = AsyncMock(return_value=mock_user)

        with patch('src.tenants.repository.TenantRepository') as mock_tenant_repo:
            mock_tenant_repo.return_value.get_tenant_by_id = AsyncMock(return_value=None)

            result = await auth_service.user_needs_tenant(user_id)
            assert result is True

    @pytest.mark.asyncio
    async def test_user_needs_tenant_has_tenant(self, auth_service):
        """Test tenant check for user with valid tenant."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        mock_user = Mock(
            tenant_id=tenant_id,
            status=UserStatus.ACTIVE
        )
        auth_service.user_repo.get_user_by_id = AsyncMock(return_value=mock_user)

        with patch('src.tenants.repository.TenantRepository') as mock_tenant_repo:
            mock_tenant_repo.return_value.get_tenant_by_id = AsyncMock(return_value=Mock(id=tenant_id))

            result = await auth_service.user_needs_tenant(user_id)
            assert result is False

    @pytest.mark.asyncio
    async def test_link_user_to_tenant_success(self, auth_service):
        """Test successful user-tenant linking."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        mock_user = Mock(id=user_id)
        updated_user = Mock(
            id=user_id,
            tenant_id=tenant_id,
            status=UserStatus.ACTIVE
        )

        auth_service.user_repo.get_user_by_id = AsyncMock(side_effect=[mock_user, updated_user])
        auth_service.user_repo.update_user_profile = AsyncMock()

        # Execute
        result = await auth_service.link_user_to_tenant(user_id, tenant_id)

        # Verify
        assert result.id == user_id
        auth_service.user_repo.update_user_profile.assert_called_once_with(
            user_id,
            {
                "tenant_id": tenant_id,
                "status": UserStatus.ACTIVE
            }
        )

    @pytest.mark.asyncio
    async def test_link_user_to_tenant_user_not_found(self, auth_service):
        """Test linking non-existent user to tenant."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        auth_service.user_repo.get_user_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await auth_service.link_user_to_tenant(user_id, tenant_id)


class TestAuthServiceConfiguration:
    """Test auth service configuration and utility methods."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service with mocked dependencies."""
        return AuthService()

    def test_is_local_auth_enabled(self, auth_service):
        """Test local auth enabled check."""
        result = auth_service.is_local_auth_enabled()
        assert result is True

    def test_get_auth_providers(self, auth_service):
        """Test auth providers configuration."""
        result = auth_service.get_auth_providers()

        assert isinstance(result, dict)
        assert result["local"] is True
        assert result["azure_ad"] is False
        assert result["google"] is False
        assert result["saml"] is False
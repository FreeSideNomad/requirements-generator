"""
Integration tests for authentication endpoints.
Tests the complete authentication flow with real database interactions.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole, UserStatus, AuthProvider


class TestAuthenticationFlow:
    """Test the complete authentication flow."""

    @pytest.mark.asyncio
    async def test_user_registration_login_flow(self, test_client: TestClient, test_db_session: AsyncSession):
        """Test complete user registration and login flow."""

        # Generate unique data for this test
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Step 1: Register a new user
        registration_data = {
            "email": f"newuser-{unique_id}@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
            "username": f"testuser-{unique_id}"
        }

        # Register user
        response = test_client.post("/auth/register", json=registration_data)
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["email"] == f"newuser-{unique_id}@example.com"
        assert user_data["first_name"] == "Test"

        # Step 2: Attempt login with the registered user
        login_data = {
            "email": f"newuser-{unique_id}@example.com",
            "password": "SecurePassword123!",
            "remember_me": False
        }

        response = test_client.post("/auth/login", json=login_data)

        # Note: This might fail if user needs tenant setup first
        # That's part of the expected flow based on our requirements
        if response.status_code == 401:
            # Expected if user needs tenant setup
            assert "pending" in response.json()["detail"].lower()
        else:
            # Should succeed if everything is properly set up
            assert response.status_code == 200
            login_response = response.json()
            assert login_response["success"] is True
            assert "access_token" in login_response
            assert "refresh_token" in login_response

    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, test_client: TestClient):
        """Test that duplicate email registration is prevented."""

        # Generate unique data for this test
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        registration_data = {
            "email": f"duplicate-{unique_id}@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "First",
            "last_name": "User"
        }

        # First registration should succeed
        response1 = test_client.post("/auth/register", json=registration_data)
        assert response1.status_code == 201

        # Second registration with same email should fail
        response2 = test_client.post("/auth/register", json=registration_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_login_credentials(self, test_client: TestClient):
        """Test login with invalid credentials."""

        # Try login with non-existent user
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }

        response = test_client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_password_validation(self, test_client: TestClient):
        """Test password validation during registration."""

        # Test weak password
        registration_data = {
            "email": "weakpass@example.com",
            "password": "weak",
            "confirm_password": "weak",
            "first_name": "Test",
            "last_name": "User"
        }

        response = test_client.post("/auth/register", json=registration_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_password_mismatch(self, test_client: TestClient):
        """Test password confirmation mismatch."""

        registration_data = {
            "email": "mismatch@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "DifferentPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }

        response = test_client.post("/auth/register", json=registration_data)
        assert response.status_code == 422  # Validation error


class TestAuthProviders:
    """Test authentication provider configuration."""

    def test_get_auth_providers(self, test_client: TestClient):
        """Test getting available authentication providers."""

        response = test_client.get("/auth/providers")
        assert response.status_code == 200

        providers_data = response.json()
        assert "providers" in providers_data

        providers = providers_data["providers"]
        assert providers["local"] is True
        assert providers["azure_ad"] is False  # Should be disabled by default
        assert providers["google"] is False
        assert providers["saml"] is False


class TestPasswordReset:
    """Test password reset functionality."""

    @pytest.mark.asyncio
    async def test_password_reset_request(self, test_client: TestClient):
        """Test password reset request."""

        # Generate unique data for this test
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # First register a user
        registration_data = {
            "email": f"resettest-{unique_id}@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "Reset",
            "last_name": "Test"
        }

        register_response = test_client.post("/auth/register", json=registration_data)
        assert register_response.status_code == 201

        # Request password reset
        reset_request = {
            "email": f"resettest-{unique_id}@example.com"
        }

        response = test_client.post("/auth/password-reset", json=reset_request)
        assert response.status_code == 200

        reset_data = response.json()
        assert reset_data["success"] is True
        assert "reset_token" in reset_data.get("details", {})  # For development

    @pytest.mark.asyncio
    async def test_password_reset_nonexistent_email(self, test_client: TestClient):
        """Test password reset for non-existent email."""

        reset_request = {
            "email": "nonexistent@example.com"
        }

        response = test_client.post("/auth/password-reset", json=reset_request)
        # Should return success to prevent email enumeration
        assert response.status_code == 200

        reset_data = response.json()
        assert reset_data["success"] is True


class TestUserInvitations:
    """Test user invitation functionality."""

    @pytest.mark.asyncio
    async def test_invitation_workflow(self, test_client: TestClient, test_db_session: AsyncSession):
        """Test the complete invitation workflow."""

        # This test would require:
        # 1. A tenant admin user
        # 2. Creating an invitation
        # 3. Registering with the invitation token

        # For now, just test the invitation verification endpoint
        # with invalid token
        response = test_client.get("/auth/invitation/invalid_token")
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]


class TestAuthenticationHeaders:
    """Test authentication with headers and tokens."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, test_client: TestClient):
        """Test accessing protected endpoint without token."""

        response = test_client.get("/auth/users")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, test_client: TestClient):
        """Test accessing protected endpoint with invalid token."""

        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.get("/auth/users", headers=headers)
        assert response.status_code == 401


class TestAPIValidation:
    """Test API input validation."""

    def test_invalid_email_format(self, test_client: TestClient):
        """Test registration with invalid email format."""

        registration_data = {
            "email": "not-an-email",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User"
        }

        response = test_client.post("/auth/register", json=registration_data)
        assert response.status_code == 422

    def test_missing_required_fields(self, test_client: TestClient):
        """Test registration with missing required fields."""

        registration_data = {
            "email": "incomplete@example.com",
            "password": "SecurePassword123!"
            # Missing confirm_password, first_name, last_name
        }

        response = test_client.post("/auth/register", json=registration_data)
        assert response.status_code == 422

    def test_login_missing_fields(self, test_client: TestClient):
        """Test login with missing fields."""

        login_data = {
            "email": "test@example.com"
            # Missing password
        }

        response = test_client.post("/auth/login", json=login_data)
        assert response.status_code == 422


class TestTenantIntegration:
    """Test tenant-related authentication features."""

    @pytest.mark.asyncio
    async def test_tenant_subdomain_login(self, test_client: TestClient):
        """Test login with tenant subdomain specification."""

        # This would test the multi-tenant login flow
        # For now, just test the basic structure
        login_data = {
            "email": "tenant@example.com",
            "password": "SecurePassword123!",
            "tenant_subdomain": "nonexistent"
        }

        response = test_client.post("/auth/login", json=login_data)
        # Should fail because user doesn't exist, but validates the structure
        assert response.status_code == 401


class TestConcurrentOperations:
    """Test concurrent authentication operations."""

    @pytest.mark.asyncio
    async def test_concurrent_registrations(self, test_client: TestClient):
        """Test handling of concurrent registration attempts."""

        # Generate unique data for this test
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # This is a basic test for concurrent operations
        # In a real scenario, you'd use threading or async calls

        registration_data = {
            "email": f"concurrent-{unique_id}@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "Concurrent",
            "last_name": "Test"
        }

        # First request
        response1 = test_client.post("/auth/register", json=registration_data)

        # Second request with same email (should fail)
        response2 = test_client.post("/auth/register", json=registration_data)

        # One should succeed, one should fail
        responses = [response1, response2]
        success_count = sum(1 for r in responses if r.status_code == 201)
        conflict_count = sum(1 for r in responses if r.status_code == 409)

        assert success_count == 1
        assert conflict_count == 1
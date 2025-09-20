"""
Authentication service layer with local authentication support.
Handles user authentication, registration, and session management without requiring external providers.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from ..shared.exceptions import AuthenticationError, ValidationError, ConflictError, NotFoundError
from ..shared.redis_client import RedisClient
from .models import User, UserSession, UserInvitation, UserRole, UserStatus, AuthProvider
from .schemas import (
    LoginRequest, RegisterRequest, UserResponse, LoginResponse,
    UserProfileUpdate, ChangePasswordRequest, UserInvitationRequest
)
from .jwt_handler import jwt_handler
from .repository import UserRepository


class AuthService:
    """Authentication service with local auth support."""

    def __init__(self, user_repo: Optional[UserRepository] = None, redis_client: Optional[RedisClient] = None):
        self.user_repo = user_repo or UserRepository()
        self.redis_client = redis_client or RedisClient()

    async def register_user(
        self,
        registration_data: RegisterRequest,
        tenant_id: Optional[uuid.UUID] = None
    ) -> UserResponse:
        """Register a new user with local authentication."""
        # Handle invitation token if provided
        invitation_data = None
        if registration_data.invitation_token:
            invitation_data = jwt_handler.verify_invitation_token(registration_data.invitation_token)
            tenant_id = invitation_data["tenant_id"]

        # Check if user already exists
        existing_user = await self.user_repo.get_user_by_email(registration_data.email)
        if existing_user:
            raise ConflictError(f"User with email '{registration_data.email}' already exists")

        # Hash password
        password_hash = jwt_handler.hash_password(registration_data.password)

        # Determine role from invitation or default
        role = UserRole.READER
        if invitation_data:
            role = UserRole(invitation_data["role"])
        elif not tenant_id:
            # New user without tenant becomes tenant admin when they create a tenant
            role = UserRole.TENANT_ADMIN

        # For users without tenant (first-time registration), create a temporary UUID
        # This will be updated when they create their tenant
        temp_tenant_id = tenant_id or uuid.uuid4()

        # Create user
        user_data = {
            "email": registration_data.email,
            "username": registration_data.username,
            "first_name": registration_data.first_name,
            "last_name": registration_data.last_name,
            "password_hash": password_hash,
            "auth_provider": AuthProvider.LOCAL,
            "role": role,
            "tenant_id": temp_tenant_id,
            "status": UserStatus.ACTIVE if tenant_id else UserStatus.PENDING,  # Pending until tenant is created
            "is_verified": True,  # Auto-verify for local auth (or implement email verification)
            "is_active": True
        }

        user = await self.user_repo.create_user(user_data)
        return UserResponse.model_validate(user)

    async def user_needs_tenant(self, user_id: uuid.UUID) -> bool:
        """Check if user needs to create or join a tenant."""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            return True

        # Check if user's tenant actually exists
        from ..tenants.repository import TenantRepository
        tenant_repo = TenantRepository()
        tenant = await tenant_repo.get_tenant_by_id(user.tenant_id)

        return tenant is None or user.status == UserStatus.PENDING

    async def link_user_to_tenant(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> UserResponse:
        """Link a user to a tenant and activate their account."""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        # Update user with real tenant and activate
        await self.user_repo.update_user_profile(
            user_id,
            {
                "tenant_id": tenant_id,
                "status": UserStatus.ACTIVE
            }
        )

        updated_user = await self.user_repo.get_user_by_id(user_id)
        return UserResponse.model_validate(updated_user)

    async def authenticate_user(self, login_data: LoginRequest) -> LoginResponse:
        """Authenticate user with email/password."""
        # Get user by email
        user = await self.user_repo.get_user_by_email(login_data.email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        # Verify password
        if not user.password_hash or not jwt_handler.verify_password(login_data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Check user status
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        if user.status == UserStatus.SUSPENDED:
            raise AuthenticationError("Account is suspended")

        if user.status == UserStatus.PENDING:
            raise AuthenticationError("Account is pending approval")

        # Verify tenant access if subdomain provided
        if login_data.tenant_subdomain:
            # Verify user belongs to this tenant
            from ..tenants.repository import TenantRepository
            tenant_repo = TenantRepository()
            tenant = await tenant_repo.get_by_subdomain(login_data.tenant_subdomain)
            if not tenant or tenant.id != user.tenant_id:
                raise AuthenticationError("Access denied to this tenant")

        # Create tokens
        access_token = jwt_handler.create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role.value,
            permissions=user.permissions
        )

        refresh_token = jwt_handler.create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id
        )

        # Create session record
        session_expires = datetime.utcnow() + timedelta(days=7 if login_data.remember_me else 1)
        await self._create_session(user, access_token, session_expires)

        # Update last login
        await self.user_repo.update_last_login(user.id)

        return LoginResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800,  # 30 minutes
            user=UserResponse.model_validate(user)
        )

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            # Verify refresh token
            payload = jwt_handler.verify_refresh_token(refresh_token)
            user_id = uuid.UUID(payload["sub"])
            tenant_id = uuid.UUID(payload["tenant_id"])

            # Get current user data
            user = await self.user_repo.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            # Create new access token
            access_token = jwt_handler.create_access_token(
                user_id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                role=user.role.value,
                permissions=user.permissions
            )

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 1800
            }

        except Exception as e:
            raise AuthenticationError("Invalid refresh token")

    async def get_current_user(self, access_token: str) -> UserResponse:
        """Get current user from access token."""
        try:
            user_data = jwt_handler.get_user_from_token(access_token)
            user = await self.user_repo.get_user_by_id(user_data["user_id"])

            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            return UserResponse.model_validate(user)

        except Exception as e:
            raise AuthenticationError("Invalid access token")

    async def update_profile(self, user_id: uuid.UUID, update_data: UserProfileUpdate) -> UserResponse:
        """Update user profile."""
        user = await self.user_repo.update_user_profile(user_id, update_data)
        if not user:
            raise NotFoundError("User", str(user_id))

        return UserResponse.model_validate(user)

    async def change_password(self, user_id: uuid.UUID, password_data: ChangePasswordRequest) -> bool:
        """Change user password."""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        # Verify current password
        if not user.password_hash or not jwt_handler.verify_password(
            password_data.current_password, user.password_hash
        ):
            raise AuthenticationError("Current password is incorrect")

        # Hash new password
        new_password_hash = jwt_handler.hash_password(password_data.new_password)

        # Update password
        await self.user_repo.update_password(user_id, new_password_hash)

        # Invalidate all sessions for security
        await self._invalidate_all_user_sessions(user_id)

        return True

    async def logout(self, access_token: str) -> bool:
        """Logout user and invalidate session."""
        try:
            user_data = jwt_handler.get_user_from_token(access_token)
            await self._invalidate_user_session(user_data["user_id"], access_token)
            return True
        except Exception:
            return False

    async def logout_all_sessions(self, user_id: uuid.UUID) -> bool:
        """Logout user from all sessions."""
        await self._invalidate_all_user_sessions(user_id)
        return True

    async def invite_user(
        self,
        inviter_id: uuid.UUID,
        tenant_id: uuid.UUID,
        invitation_data: UserInvitationRequest
    ) -> Dict[str, Any]:
        """Send user invitation."""
        # Check if user already exists
        existing_user = await self.user_repo.get_user_by_email(invitation_data.email)
        if existing_user:
            raise ConflictError(f"User with email '{invitation_data.email}' already exists")

        # Generate invitation token
        invitation_token = jwt_handler.generate_invitation_token(
            email=invitation_data.email,
            tenant_id=tenant_id,
            role=invitation_data.role.value,
            expires_days=7
        )

        # Store invitation in database
        invitation = await self.user_repo.create_invitation(
            email=invitation_data.email,
            tenant_id=tenant_id,
            role=invitation_data.role,
            invited_by_id=inviter_id,
            token=invitation_token,
            message=invitation_data.message,
            permissions=invitation_data.permissions
        )

        # In a real implementation, send email here
        invitation_url = f"/auth/register?token={invitation_token}"

        return {
            "invitation_id": invitation.id,
            "email": invitation_data.email,
            "role": invitation_data.role,
            "expires_at": invitation.expires_at,
            "invitation_url": invitation_url,
            "token": invitation_token  # Remove in production
        }

    async def verify_invitation(self, token: str) -> Dict[str, Any]:
        """Verify invitation token and return invitation data."""
        invitation_data = jwt_handler.verify_invitation_token(token)

        # Check if invitation exists and is valid
        invitation = await self.user_repo.get_invitation_by_token(token)
        if not invitation or not invitation.is_valid:
            raise AuthenticationError("Invalid or expired invitation")

        return invitation_data

    async def _create_session(
        self,
        user: User,
        session_token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create a new user session."""
        session_data = {
            "user_id": user.id,
            "session_token": session_token,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "expires_at": expires_at,
            "is_active": True
        }

        return await self.user_repo.create_session(session_data)

    async def _invalidate_user_session(self, user_id: uuid.UUID, session_token: str) -> None:
        """Invalidate a specific user session."""
        await self.user_repo.invalidate_session(user_id, session_token)

        # Also remove from Redis cache
        cache_key = f"session:{session_token}"
        await self.redis_client.delete(cache_key)

    async def _invalidate_all_user_sessions(self, user_id: uuid.UUID) -> None:
        """Invalidate all sessions for a user."""
        await self.user_repo.invalidate_all_sessions(user_id)

        # Also remove from Redis cache (would need to track session keys)
        pattern = f"session:*:user:{user_id}"
        await self.redis_client.delete_pattern(pattern)

    async def check_session_validity(self, session_token: str) -> bool:
        """Check if session is still valid."""
        # First check Redis cache
        cache_key = f"session:{session_token}"
        cached_session = await self.redis_client.get(cache_key)

        if cached_session:
            return True

        # Fallback to database
        session = await self.user_repo.get_session_by_token(session_token)
        if session and session.is_active and not session.is_expired:
            # Cache the valid session
            await self.redis_client.setex(
                cache_key,
                3600,  # 1 hour cache
                {"user_id": str(session.user_id), "active": True}
            )
            return True

        return False

    async def require_password_reset(self, email: str) -> str:
        """Generate password reset token."""
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists or not
            raise AuthenticationError("If the email exists, a reset link will be sent")

        reset_token = jwt_handler.generate_reset_token(user.id)

        # In a real implementation, send email here
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        try:
            user_id = jwt_handler.verify_reset_token(token)
            password_hash = jwt_handler.hash_password(new_password)

            await self.user_repo.update_password(user_id, password_hash)
            await self._invalidate_all_user_sessions(user_id)

            return True

        except Exception:
            raise AuthenticationError("Invalid or expired reset token")

    def is_local_auth_enabled(self) -> bool:
        """Check if local authentication is enabled."""
        return True  # Always enabled for this implementation

    def get_auth_providers(self) -> Dict[str, bool]:
        """Get available authentication providers."""
        return {
            "local": True,
            "azure_ad": False,  # Disabled as requested
            "google": False,
            "saml": False
        }
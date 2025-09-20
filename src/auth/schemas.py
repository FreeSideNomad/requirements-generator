"""
Authentication Pydantic schemas for API validation and serialization.
Handles login, registration, and user management requests.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field, EmailStr, validator

from ..shared.models import BaseEntity, BaseResponse
from .models import UserRole, UserStatus, AuthProvider


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="User password")
    tenant_subdomain: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=63,
        description="Tenant subdomain (optional if user belongs to only one tenant)"
    )
    remember_me: bool = Field(default=False, description="Extended session duration")

    @validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="User password")
    confirm_password: str = Field(min_length=8, max_length=128, description="Password confirmation")
    first_name: str = Field(min_length=1, max_length=100, description="First name")
    last_name: str = Field(min_length=1, max_length=100, description="Last name")
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username (optional)"
    )
    invitation_token: Optional[str] = Field(
        default=None,
        description="Invitation token for tenant access"
    )

    @validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate that passwords match."""
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password complexity requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit"
            )

        return v


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr = Field(description="User email address")
    tenant_subdomain: Optional[str] = Field(
        default=None,
        description="Tenant subdomain (optional)"
    )


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str = Field(description="Password reset token")
    new_password: str = Field(min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(min_length=8, max_length=128, description="Password confirmation")

    @validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate that passwords match."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str = Field(description="Refresh token")


class UserResponse(BaseEntity):
    """User response schema for API responses."""

    email: str
    username: Optional[str]
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    auth_provider: AuthProvider
    is_active: bool
    is_verified: bool
    tenant_id: uuid.UUID
    avatar_url: Optional[str]
    timezone: str
    locale: str
    last_login_at: Optional[datetime]
    permissions: Dict[str, Any]

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        return self.username or self.full_name or self.email


class LoginResponse(BaseResponse):
    """Login response schema."""

    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    user: UserResponse = Field(description="User information")


class RefreshResponse(BaseResponse):
    """Token refresh response schema."""

    access_token: str = Field(description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")


class UserProfileUpdate(BaseModel):
    """User profile update schema."""

    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Last name"
    )
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Avatar image URL"
    )
    timezone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="User timezone"
    )
    locale: Optional[str] = Field(
        default=None,
        max_length=10,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="User locale (e.g., 'en', 'en-US')"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User preferences"
    )


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(min_length=8, max_length=128, description="Password confirmation")

    @validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate that passwords match."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class UserInvitationRequest(BaseModel):
    """User invitation request schema."""

    email: EmailStr = Field(description="Invitee email address")
    role: UserRole = Field(description="Assigned role")
    permissions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional permissions"
    )
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional invitation message"
    )


class UserInvitationResponse(BaseResponse):
    """User invitation response schema."""

    invitation_id: uuid.UUID = Field(description="Invitation ID")
    email: str = Field(description="Invitee email")
    role: UserRole = Field(description="Assigned role")
    expires_at: datetime = Field(description="Invitation expiration")
    invitation_url: str = Field(description="Invitation acceptance URL")


class SessionInfo(BaseModel):
    """Session information schema."""

    session_id: uuid.UUID = Field(description="Session ID")
    user_id: uuid.UUID = Field(description="User ID")
    ip_address: Optional[str] = Field(description="IP address")
    user_agent: Optional[str] = Field(description="User agent string")
    created_at: datetime = Field(description="Session creation time")
    last_activity_at: datetime = Field(description="Last activity time")
    expires_at: datetime = Field(description="Session expiration time")
    is_active: bool = Field(description="Session active status")


class APIKeyRequest(BaseModel):
    """API key creation request schema."""

    name: str = Field(min_length=1, max_length=100, description="API key name")
    permissions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="API key permissions"
    )


class APIKeyResponse(BaseResponse):
    """API key creation response schema."""

    key_id: uuid.UUID = Field(description="API key ID")
    name: str = Field(description="API key name")
    key: str = Field(description="API key value (shown only once)")
    prefix: str = Field(description="Key prefix for identification")
    permissions: Dict[str, Any] = Field(description="Granted permissions")
    created_at: datetime = Field(description="Creation timestamp")


class APIKeyInfo(BaseModel):
    """API key information schema (without key value)."""

    key_id: uuid.UUID = Field(description="API key ID")
    name: str = Field(description="API key name")
    prefix: str = Field(description="Key prefix")
    permissions: Dict[str, Any] = Field(description="Granted permissions")
    created_at: datetime = Field(description="Creation timestamp")
    last_used: Optional[datetime] = Field(description="Last usage timestamp")
    is_active: bool = Field(description="Key active status")


class TwoFactorSetupRequest(BaseModel):
    """Two-factor authentication setup request."""

    password: str = Field(description="Current password for verification")


class TwoFactorConfirmRequest(BaseModel):
    """Two-factor authentication confirmation request."""

    totp_code: str = Field(min_length=6, max_length=6, description="TOTP verification code")
    backup_codes: bool = Field(default=True, description="Generate backup codes")


class TwoFactorVerifyRequest(BaseModel):
    """Two-factor authentication verification request."""

    code: str = Field(min_length=6, max_length=8, description="TOTP code or backup code")
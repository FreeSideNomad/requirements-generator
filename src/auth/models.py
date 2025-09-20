"""
Authentication and user management models.
Supports role-based access control with multi-tenant isolation.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..shared.database import Base


class UserRole(str, Enum):
    """User role hierarchy for RBAC."""
    SUPER_ADMIN = "super_admin"     # Platform administrator
    TENANT_ADMIN = "tenant_admin"   # Tenant administrator
    TEAM_LEAD = "team_lead"         # Team leader
    CONTRIBUTOR = "contributor"     # Regular user
    READER = "reader"               # Read-only access


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AuthProvider(str, Enum):
    """Supported authentication providers."""
    LOCAL = "local"
    AZURE_AD = "azure_ad"
    GOOGLE = "google"
    SAML = "saml"


class User(Base):
    """
    Core user model with multi-tenant support and RBAC.
    Users belong to a tenant and have specific roles within that tenant.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic user information
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(50))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Authentication
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))  # For local auth
    auth_provider: Mapped[AuthProvider] = mapped_column(SQLEnum(AuthProvider), default=AuthProvider.LOCAL)
    external_id: Mapped[Optional[str]] = mapped_column(String(255))  # For external auth

    # Account status
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus), default=UserStatus.PENDING)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Multi-tenant relationship
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False
    )

    # Role and permissions
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.READER)
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Profile information
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    locale: Mapped[str] = mapped_column(String(10), default="en")

    # User preferences
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'username', name='uq_tenant_username'),
        UniqueConstraint('tenant_id', 'external_id', name='uq_tenant_external_id'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        return self.username or self.full_name or self.email

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        # Super admin has all permissions
        if self.role == UserRole.SUPER_ADMIN:
            return True

        # Check explicit permissions
        return self.permissions.get(permission, False)

    def has_role_level(self, required_role: UserRole) -> bool:
        """Check if user has sufficient role level."""
        role_hierarchy = {
            UserRole.SUPER_ADMIN: 4,
            UserRole.TENANT_ADMIN: 3,
            UserRole.TEAM_LEAD: 2,
            UserRole.CONTRIBUTOR: 1,
            UserRole.READER: 0
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.preferences.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value


class UserSession(Base):
    """
    User session tracking for security and analytics.
    Supports session management and concurrent login tracking.
    """
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    # Session identification
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True)

    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    device_info: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Session lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    terminated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    def extend_session(self, hours: int = 24) -> None:
        """Extend session expiration."""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity_at = datetime.utcnow()


class UserInvitation(Base):
    """
    User invitation model for tenant user onboarding.
    Tracks invitation lifecycle and role assignment.
    """
    __tablename__ = "user_invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Invitation details
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Tenant and role assignment
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False
    )
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.READER)
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Invitation metadata
    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    message: Mapped[Optional[str]] = mapped_column(Text)

    # Status tracking
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    invited_by: Mapped["User"] = relationship("User", foreign_keys=[invited_by_id])
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<UserInvitation(id={self.id}, email='{self.email}', role='{self.role}')>"

    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid."""
        if self.is_used or self.is_expired:
            return False
        return datetime.utcnow() < self.expires_at


class AuditLog(Base):
    """
    Audit logging for security and compliance.
    Tracks user actions across the platform.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Event identification
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[str]] = mapped_column(String(255))

    # User and tenant context
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id")
    )
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id")
    )

    # Event details
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Status and outcome
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, failure, error
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    tenant: Mapped[Optional["Tenant"]] = relationship("Tenant")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', action='{self.action}')>"
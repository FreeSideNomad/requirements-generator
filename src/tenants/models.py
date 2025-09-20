"""
Tenant domain models for multi-tenant SaaS architecture.
Defines tenant, subscription, and feature management.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..shared.database import Base


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class Industry(str, Enum):
    """Industry classifications for tenant templates."""
    BANKING = "banking"
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    TECHNOLOGY = "technology"
    GOVERNMENT = "government"
    EDUCATION = "education"
    RETAIL = "retail"


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class Tenant(Base):
    """
    Core tenant model for multi-tenant SaaS architecture.
    Each tenant represents an organization using the platform.
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic tenant information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True)

    # Industry and template configuration
    industry: Mapped[Industry] = mapped_column(String(50), nullable=False)
    template_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Status and lifecycle
    status: Mapped[TenantStatus] = mapped_column(String(20), default=TenantStatus.TRIAL)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Subscription information
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(String(20), default=SubscriptionTier.STARTER)
    max_users: Mapped[Optional[int]] = mapped_column(default=5)
    max_projects: Mapped[Optional[int]] = mapped_column(default=3)

    # Feature flags and customization
    features: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Contact information
    billing_email: Mapped[Optional[str]] = mapped_column(String(255))
    technical_contact: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', subdomain='{self.subdomain}')>"

    @property
    def is_trial_expired(self) -> bool:
        """Check if trial period has expired."""
        if self.status != TenantStatus.TRIAL or not self.trial_ends_at:
            return False
        return datetime.utcnow() > self.trial_ends_at

    @property
    def display_name(self) -> str:
        """Get display name for the tenant."""
        return self.name

    def has_feature(self, feature: str) -> bool:
        """Check if tenant has access to a specific feature."""
        return self.features.get(feature, False)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a tenant-specific setting."""
        return self.settings.get(key, default)


class TenantInvitation(Base):
    """
    Tenant invitation model for onboarding new tenants.
    Tracks invitation lifecycle and validation.
    """
    __tablename__ = "tenant_invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Invitation details
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Tenant configuration
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(63), nullable=False)
    industry: Mapped[Industry] = mapped_column(String(50), nullable=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(String(20), default=SubscriptionTier.STARTER)

    # Status tracking
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<TenantInvitation(id={self.id}, email='{self.email}', tenant_name='{self.tenant_name}')>"

    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid."""
        if self.is_used or self.is_expired:
            return False
        return datetime.utcnow() < self.expires_at


class TenantFeature(Base):
    """
    Feature flag management for tenants.
    Allows granular control over feature access.
    """
    __tablename__ = "tenant_features"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False
    )

    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Feature configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Usage limits
    usage_limit: Mapped[Optional[int]] = mapped_column()
    usage_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'feature_name', name='uq_tenant_feature'),
    )

    def __repr__(self) -> str:
        return f"<TenantFeature(tenant_id={self.tenant_id}, feature='{self.feature_name}', enabled={self.is_enabled})>"

    @property
    def is_available(self) -> bool:
        """Check if feature is currently available."""
        if not self.is_enabled:
            return False

        # Check expiration
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        # Check usage limits
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False

        return True

    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1
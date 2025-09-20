"""
Tenant Pydantic schemas for API validation and serialization.
Handles tenant creation, updates, and response formatting.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field, validator

from ..shared.models import BaseEntity, BaseResponse, PaginatedListResponse
from .models import TenantStatus, Industry, SubscriptionTier


class TenantBase(BaseModel):
    """Base tenant schema with common fields."""

    name: str = Field(min_length=1, max_length=255, description="Tenant organization name")
    subdomain: str = Field(
        min_length=3,
        max_length=63,
        pattern=r"^[a-z0-9]([a-z0-9\-]{1,61}[a-z0-9])?$",
        description="Unique subdomain for tenant"
    )
    custom_domain: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Custom domain (optional)"
    )
    industry: Industry = Field(description="Industry classification")
    billing_email: Optional[str] = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Billing contact email"
    )
    technical_contact: Optional[str] = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Technical contact email"
    )

    @validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        """Validate subdomain format and reserved names."""
        v = v.lower()

        # Reserved subdomains
        reserved = {
            "www", "api", "admin", "app", "mail", "email", "ftp", "ssh",
            "staging", "test", "dev", "demo", "beta", "alpha", "support",
            "help", "docs", "blog", "status", "security", "billing"
        }

        if v in reserved:
            raise ValueError(f"Subdomain '{v}' is reserved")

        return v


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""

    subscription_tier: SubscriptionTier = Field(
        default=SubscriptionTier.STARTER,
        description="Initial subscription tier"
    )
    max_users: Optional[int] = Field(
        default=5,
        ge=1,
        le=10000,
        description="Maximum number of users"
    )
    max_projects: Optional[int] = Field(
        default=3,
        ge=1,
        le=1000,
        description="Maximum number of projects"
    )
    template_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Industry template configuration"
    )
    features: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Feature flags and settings"
    )
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Tenant-specific settings"
    )


class TenantUpdate(BaseModel):
    """Schema for updating an existing tenant."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Tenant organization name"
    )
    custom_domain: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Custom domain"
    )
    industry: Optional[Industry] = Field(default=None, description="Industry classification")
    status: Optional[TenantStatus] = Field(default=None, description="Tenant status")
    subscription_tier: Optional[SubscriptionTier] = Field(
        default=None,
        description="Subscription tier"
    )
    max_users: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Maximum number of users"
    )
    max_projects: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="Maximum number of projects"
    )
    billing_email: Optional[str] = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Billing contact email"
    )
    technical_contact: Optional[str] = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Technical contact email"
    )
    template_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Industry template configuration"
    )
    features: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Feature flags and settings"
    )
    settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Tenant-specific settings"
    )


class TenantResponse(BaseEntity):
    """Schema for tenant API responses."""

    name: str
    subdomain: str
    custom_domain: Optional[str]
    industry: Industry
    status: TenantStatus
    is_active: bool
    subscription_tier: SubscriptionTier
    max_users: Optional[int]
    max_projects: Optional[int]
    billing_email: Optional[str]
    technical_contact: Optional[str]
    template_config: Dict[str, Any]
    features: Dict[str, Any]
    settings: Dict[str, Any]
    trial_ends_at: Optional[datetime]
    suspended_at: Optional[datetime]

    # Computed properties
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


class TenantSummary(BaseModel):
    """Lightweight tenant summary for listings."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    subdomain: str
    industry: Industry
    status: TenantStatus
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime


class TenantListResponse(PaginatedListResponse):
    """Paginated tenant list response."""

    data: List[TenantSummary] = Field(description="List of tenant summaries")


class TenantCreateResponse(BaseResponse):
    """Response for tenant creation."""

    tenant: TenantResponse = Field(description="Created tenant details")


class TenantUpdateResponse(BaseResponse):
    """Response for tenant updates."""

    tenant: TenantResponse = Field(description="Updated tenant details")


class TenantStatsResponse(BaseModel):
    """Tenant usage statistics."""

    model_config = {"from_attributes": True}

    tenant_id: uuid.UUID
    current_users: int = Field(description="Current number of users")
    current_projects: int = Field(description="Current number of projects")
    storage_used_mb: float = Field(description="Storage used in MB")
    api_calls_today: int = Field(description="API calls made today")
    last_activity: Optional[datetime] = Field(description="Last activity timestamp")

    # Limits and usage percentages
    @property
    def users_usage_percent(self) -> Optional[float]:
        """Calculate user usage percentage."""
        return None  # To be calculated based on tenant limits

    @property
    def projects_usage_percent(self) -> Optional[float]:
        """Calculate projects usage percentage."""
        return None  # To be calculated based on tenant limits


class IndustryTemplate(BaseModel):
    """Industry template configuration schema."""

    industry: Industry
    name: str = Field(description="Template display name")
    description: str = Field(description="Template description")
    features: Dict[str, Any] = Field(description="Default feature settings")
    settings: Dict[str, Any] = Field(description="Default tenant settings")
    requirements_templates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Pre-configured requirement templates"
    )
    compliance_frameworks: List[str] = Field(
        default_factory=list,
        description="Relevant compliance frameworks"
    )


class IndustryTemplateListResponse(BaseModel):
    """Response for industry template listings."""

    templates: List[IndustryTemplate] = Field(description="Available industry templates")
"""
Tenant business logic and service layer.
Handles tenant operations, industry templates, and business rules.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from ..shared.exceptions import ValidationError, ConflictError, NotFoundError
from .models import Tenant, Industry, SubscriptionTier, TenantStatus
from .schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantSummary,
    TenantStatsResponse, IndustryTemplate
)
from .repository import TenantRepository


class TenantService:
    """Service layer for tenant business logic."""

    def __init__(self, tenant_repo: Optional[TenantRepository] = None):
        self.tenant_repo = tenant_repo or TenantRepository()

    async def create_tenant(self, tenant_data: TenantCreate) -> TenantResponse:
        """Create a new tenant with industry template configuration."""
        # Apply industry template
        template = self.get_industry_template(tenant_data.industry)
        if template:
            # Merge template configuration with provided data
            tenant_data.features = {**template.features, **(tenant_data.features or {})}
            tenant_data.settings = {**template.settings, **(tenant_data.settings or {})}
            tenant_data.template_config = {
                **template.model_dump(),
                **(tenant_data.template_config or {})
            }

        # Create tenant
        tenant = await self.tenant_repo.create_tenant(tenant_data)

        return TenantResponse.model_validate(tenant)

    async def get_tenant(self, tenant_id: uuid.UUID) -> Optional[TenantResponse]:
        """Get tenant by ID."""
        tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
        if not tenant:
            return None

        return TenantResponse.model_validate(tenant)

    async def get_tenant_by_subdomain(self, subdomain: str) -> Optional[TenantResponse]:
        """Get tenant by subdomain."""
        tenant = await self.tenant_repo.get_by_subdomain(subdomain)
        if not tenant:
            return None

        return TenantResponse.model_validate(tenant)

    async def update_tenant(self, tenant_id: uuid.UUID, update_data: TenantUpdate) -> TenantResponse:
        """Update an existing tenant."""
        tenant = await self.tenant_repo.update_tenant(tenant_id, update_data)
        if not tenant:
            raise NotFoundError("Tenant", str(tenant_id))

        return TenantResponse.model_validate(tenant)

    async def delete_tenant(self, tenant_id: uuid.UUID) -> bool:
        """Delete (deactivate) a tenant."""
        return await self.tenant_repo.delete_tenant(tenant_id)

    async def list_tenants(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[TenantStatus] = None,
        industry: Optional[Industry] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> Tuple[List[TenantSummary], int]:
        """List tenants with filtering and pagination."""
        if page < 1:
            raise ValidationError("Page number must be >= 1")

        if page_size < 1 or page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")

        skip = (page - 1) * page_size

        tenants, total = await self.tenant_repo.list_tenants(
            skip=skip,
            limit=page_size,
            status=status,
            industry=industry,
            subscription_tier=subscription_tier,
            search=search,
            active_only=active_only
        )

        tenant_summaries = [TenantSummary.model_validate(tenant) for tenant in tenants]

        return tenant_summaries, total

    async def get_tenant_stats(self, tenant_id: uuid.UUID) -> TenantStatsResponse:
        """Get tenant usage statistics."""
        stats = await self.tenant_repo.get_tenant_stats(tenant_id)
        return TenantStatsResponse.model_validate(stats)

    async def activate_tenant(self, tenant_id: uuid.UUID) -> TenantResponse:
        """Activate a suspended tenant."""
        tenant = await self.tenant_repo.activate_tenant(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant", str(tenant_id))

        return TenantResponse.model_validate(tenant)

    async def suspend_tenant(
        self,
        tenant_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> TenantResponse:
        """Suspend a tenant."""
        tenant = await self.tenant_repo.suspend_tenant(tenant_id, reason)
        if not tenant:
            raise NotFoundError("Tenant", str(tenant_id))

        return TenantResponse.model_validate(tenant)

    async def upgrade_subscription(
        self,
        tenant_id: uuid.UUID,
        new_tier: SubscriptionTier,
        max_users: Optional[int] = None,
        max_projects: Optional[int] = None
    ) -> TenantResponse:
        """Upgrade tenant subscription."""
        # Get subscription limits based on tier
        limits = self._get_subscription_limits(new_tier)

        update_data = TenantUpdate(
            subscription_tier=new_tier,
            max_users=max_users or limits["max_users"],
            max_projects=max_projects or limits["max_projects"],
            status=TenantStatus.ACTIVE  # Activate if upgrading from trial
        )

        return await self.update_tenant(tenant_id, update_data)

    def get_industry_template(self, industry: Industry) -> Optional[IndustryTemplate]:
        """Get industry-specific template configuration."""
        templates = {
            Industry.BANKING: IndustryTemplate(
                industry=Industry.BANKING,
                name="Banking & Financial Services",
                description="Template for banking and financial services organizations",
                features={
                    "compliance_tracking": True,
                    "audit_trails": True,
                    "data_encryption": True,
                    "role_based_access": True,
                    "document_versioning": True,
                    "regulatory_reporting": True
                },
                settings={
                    "security_level": "high",
                    "data_retention_days": 2555,  # 7 years
                    "approval_required": True,
                    "encryption_at_rest": True,
                    "multi_factor_auth": True
                },
                compliance_frameworks=["SOX", "PCI DSS", "Basel III", "GDPR"],
                requirements_templates=[
                    {
                        "name": "Account Management System",
                        "type": "epic",
                        "description": "Customer account management and maintenance"
                    },
                    {
                        "name": "Transaction Processing",
                        "type": "epic",
                        "description": "Real-time transaction processing system"
                    },
                    {
                        "name": "Regulatory Reporting",
                        "type": "epic",
                        "description": "Automated regulatory compliance reporting"
                    }
                ]
            ),
            Industry.HEALTHCARE: IndustryTemplate(
                industry=Industry.HEALTHCARE,
                name="Healthcare & Medical",
                description="Template for healthcare and medical organizations",
                features={
                    "hipaa_compliance": True,
                    "audit_trails": True,
                    "data_encryption": True,
                    "patient_privacy": True,
                    "access_controls": True,
                    "medical_terminology": True
                },
                settings={
                    "security_level": "high",
                    "data_retention_days": 2190,  # 6 years
                    "phi_protection": True,
                    "audit_everything": True,
                    "encryption_at_rest": True
                },
                compliance_frameworks=["HIPAA", "HITECH", "FDA 21 CFR Part 11", "GDPR"],
                requirements_templates=[
                    {
                        "name": "Patient Management System",
                        "type": "epic",
                        "description": "Electronic health records and patient management"
                    },
                    {
                        "name": "Clinical Decision Support",
                        "type": "epic",
                        "description": "AI-powered clinical decision support tools"
                    }
                ]
            ),
            Industry.TECHNOLOGY: IndustryTemplate(
                industry=Industry.TECHNOLOGY,
                name="Technology & Software",
                description="Template for technology and software companies",
                features={
                    "agile_workflows": True,
                    "ci_cd_integration": True,
                    "api_documentation": True,
                    "performance_monitoring": True,
                    "scalability_planning": True,
                    "security_by_design": True
                },
                settings={
                    "security_level": "medium",
                    "data_retention_days": 1095,  # 3 years
                    "rapid_iteration": True,
                    "automated_testing": True,
                    "continuous_deployment": True
                },
                compliance_frameworks=["SOC 2", "ISO 27001", "GDPR"],
                requirements_templates=[
                    {
                        "name": "User Authentication System",
                        "type": "epic",
                        "description": "Secure user authentication and authorization"
                    },
                    {
                        "name": "API Gateway",
                        "type": "epic",
                        "description": "Centralized API management and routing"
                    }
                ]
            ),
            Industry.GOVERNMENT: IndustryTemplate(
                industry=Industry.GOVERNMENT,
                name="Government & Public Sector",
                description="Template for government and public sector organizations",
                features={
                    "accessibility_compliance": True,
                    "public_transparency": True,
                    "audit_trails": True,
                    "security_clearance": True,
                    "citizen_services": True,
                    "regulatory_compliance": True
                },
                settings={
                    "security_level": "maximum",
                    "data_retention_days": 3650,  # 10 years
                    "accessibility_required": True,
                    "public_disclosure": True,
                    "security_clearance_levels": True
                },
                compliance_frameworks=["FedRAMP", "FISMA", "Section 508", "GDPR"],
                requirements_templates=[
                    {
                        "name": "Citizen Portal",
                        "type": "epic",
                        "description": "Online portal for citizen services and information"
                    },
                    {
                        "name": "Document Management",
                        "type": "epic",
                        "description": "Secure government document management system"
                    }
                ]
            )
        }

        return templates.get(industry)

    def get_all_industry_templates(self) -> List[IndustryTemplate]:
        """Get all available industry templates."""
        templates = []
        for industry in Industry:
            template = self.get_industry_template(industry)
            if template:
                templates.append(template)
        return templates

    def _get_subscription_limits(self, tier: SubscriptionTier) -> Dict[str, int]:
        """Get resource limits for subscription tier."""
        limits = {
            SubscriptionTier.STARTER: {
                "max_users": 5,
                "max_projects": 3,
                "max_storage_gb": 1,
                "api_calls_per_day": 1000
            },
            SubscriptionTier.PROFESSIONAL: {
                "max_users": 25,
                "max_projects": 15,
                "max_storage_gb": 10,
                "api_calls_per_day": 10000
            },
            SubscriptionTier.ENTERPRISE: {
                "max_users": 100,
                "max_projects": 50,
                "max_storage_gb": 100,
                "api_calls_per_day": 100000
            },
            SubscriptionTier.CUSTOM: {
                "max_users": 1000,
                "max_projects": 500,
                "max_storage_gb": 1000,
                "api_calls_per_day": 1000000
            }
        }

        return limits.get(tier, limits[SubscriptionTier.STARTER])

    async def check_tenant_limits(self, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Check if tenant is approaching or exceeding limits."""
        tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant", str(tenant_id))

        stats = await self.get_tenant_stats(tenant_id)
        limits = self._get_subscription_limits(tenant.subscription_tier)

        usage_check = {
            "tenant_id": tenant_id,
            "subscription_tier": tenant.subscription_tier,
            "limits": limits,
            "current_usage": {
                "users": stats.current_users,
                "projects": stats.current_projects,
                "storage_mb": stats.storage_used_mb
            },
            "warnings": [],
            "exceeded": []
        }

        # Check user limits
        if tenant.max_users and stats.current_users >= tenant.max_users:
            usage_check["exceeded"].append("users")
        elif tenant.max_users and stats.current_users >= tenant.max_users * 0.8:
            usage_check["warnings"].append("users")

        # Check project limits
        if tenant.max_projects and stats.current_projects >= tenant.max_projects:
            usage_check["exceeded"].append("projects")
        elif tenant.max_projects and stats.current_projects >= tenant.max_projects * 0.8:
            usage_check["warnings"].append("projects")

        return usage_check
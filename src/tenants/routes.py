"""
Tenant management API routes.
Handles tenant CRUD operations and multi-tenant context.
"""

import uuid
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from ..shared.models import BaseResponse, PaginatedListResponse
from ..shared.exceptions import ValidationError, ConflictError, NotFoundError, DatabaseError
from .schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantSummary,
    TenantListResponse, TenantCreateResponse, TenantUpdateResponse,
    TenantStatsResponse, IndustryTemplateListResponse
)
from .models import TenantStatus, Industry, SubscriptionTier
from .service import TenantService

tenants_router = APIRouter(prefix="/tenants", tags=["tenants"])


@tenants_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant_data: TenantCreate) -> TenantCreateResponse:
    """Create a new tenant with industry template configuration."""
    try:
        tenant_service = TenantService()
        tenant = await tenant_service.create_tenant(tenant_data)

        return TenantCreateResponse(
            success=True,
            message="Tenant created successfully",
            tenant=tenant
        )

    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant"
        )


@tenants_router.get("/", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[TenantStatus] = Query(None, description="Filter by status"),
    industry: Optional[Industry] = Query(None, description="Filter by industry"),
    subscription_tier: Optional[SubscriptionTier] = Query(None, description="Filter by subscription tier"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search by name or subdomain"),
    active_only: bool = Query(True, description="Show only active tenants")
) -> TenantListResponse:
    """List tenants with filtering and pagination."""
    try:
        tenant_service = TenantService()
        tenants, total = await tenant_service.list_tenants(
            page=page,
            page_size=page_size,
            status=status,
            industry=industry,
            subscription_tier=subscription_tier,
            search=search,
            active_only=active_only
        )

        # Calculate pagination metadata
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1

        return TenantListResponse(
            success=True,
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            data=tenants
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenants"
        )


@tenants_router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID = Path(description="Tenant ID")
) -> TenantResponse:
    """Get tenant details by ID."""
    try:
        tenant_service = TenantService()
        tenant = await tenant_service.get_tenant(tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

        return tenant

    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant"
        )


@tenants_router.put("/{tenant_id}", response_model=TenantUpdateResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    update_data: TenantUpdate
) -> TenantUpdateResponse:
    """Update an existing tenant."""
    try:
        tenant_service = TenantService()
        tenant = await tenant_service.update_tenant(tenant_id, update_data)

        return TenantUpdateResponse(
            success=True,
            message="Tenant updated successfully",
            tenant=tenant
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant"
        )


@tenants_router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: uuid.UUID):
    """Delete (deactivate) a tenant."""
    try:
        tenant_service = TenantService()
        success = await tenant_service.delete_tenant(tenant_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

    except HTTPException:
        raise
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tenant"
        )


@tenants_router.get("/subdomain/{subdomain}", response_model=TenantResponse)
async def get_tenant_by_subdomain(
    subdomain: str = Path(min_length=3, max_length=63, description="Tenant subdomain")
) -> TenantResponse:
    """Get tenant by subdomain."""
    try:
        tenant_service = TenantService()
        tenant = await tenant_service.get_tenant_by_subdomain(subdomain)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with subdomain '{subdomain}' not found"
            )

        return tenant

    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant"
        )


@tenants_router.get("/{tenant_id}/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(tenant_id: uuid.UUID) -> TenantStatsResponse:
    """Get tenant usage statistics."""
    try:
        tenant_service = TenantService()
        stats = await tenant_service.get_tenant_stats(tenant_id)
        return stats

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant statistics"
        )


@tenants_router.post("/{tenant_id}/activate", response_model=TenantUpdateResponse)
async def activate_tenant(tenant_id: uuid.UUID) -> TenantUpdateResponse:
    """Activate a suspended tenant."""
    try:
        tenant_service = TenantService()
        tenant = await tenant_service.activate_tenant(tenant_id)

        return TenantUpdateResponse(
            success=True,
            message="Tenant activated successfully",
            tenant=tenant
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate tenant"
        )


@tenants_router.post("/{tenant_id}/suspend", response_model=TenantUpdateResponse)
async def suspend_tenant(
    tenant_id: uuid.UUID,
    reason: Optional[str] = Query(None, description="Suspension reason")
) -> TenantUpdateResponse:
    """Suspend a tenant."""
    try:
        tenant_service = TenantService()
        tenant = await tenant_service.suspend_tenant(tenant_id, reason)

        return TenantUpdateResponse(
            success=True,
            message="Tenant suspended successfully",
            tenant=tenant
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend tenant"
        )


@tenants_router.post("/{tenant_id}/upgrade", response_model=TenantUpdateResponse)
async def upgrade_subscription(
    tenant_id: uuid.UUID,
    new_tier: SubscriptionTier,
    max_users: Optional[int] = Query(None, ge=1, le=10000),
    max_projects: Optional[int] = Query(None, ge=1, le=1000)
) -> TenantUpdateResponse:
    """Upgrade tenant subscription tier."""
    try:
        tenant_service = TenantService()
        tenant = await tenant_service.upgrade_subscription(
            tenant_id, new_tier, max_users, max_projects
        )

        return TenantUpdateResponse(
            success=True,
            message=f"Tenant upgraded to {new_tier} tier",
            tenant=tenant
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade tenant"
        )


@tenants_router.get("/{tenant_id}/limits")
async def check_tenant_limits(tenant_id: uuid.UUID) -> Dict[str, Any]:
    """Check tenant resource limits and usage."""
    try:
        tenant_service = TenantService()
        limits_check = await tenant_service.check_tenant_limits(tenant_id)
        return limits_check

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check tenant limits"
        )


@tenants_router.get("/templates/industry", response_model=IndustryTemplateListResponse)
async def get_industry_templates() -> IndustryTemplateListResponse:
    """Get all available industry templates."""
    try:
        tenant_service = TenantService()
        templates = tenant_service.get_all_industry_templates()

        return IndustryTemplateListResponse(templates=templates)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve industry templates"
        )


@tenants_router.get("/templates/industry/{industry}")
async def get_industry_template(industry: Industry) -> Dict[str, Any]:
    """Get specific industry template configuration."""
    try:
        tenant_service = TenantService()
        template = tenant_service.get_industry_template(industry)

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template for industry '{industry}' not found"
            )

        return template.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve industry template"
        )
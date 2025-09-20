"""
Requirements FastAPI routes for project and requirements management.
Handles CRUD operations, domain analysis, and documentation generation.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import Response, FileResponse

from ..auth.routes import get_current_user_dependency as get_current_user
from ..auth.schemas import UserResponse
from ..shared.exceptions import ValidationError, NotFoundError, AppException
from ..shared.dependencies import get_db_session, get_current_tenant
from ..tenants.schemas import TenantResponse
from .service import ProjectService, RequirementService, DomainService
from .markdown_generator import MarkdownGenerator
from .schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, PaginatedProjectResponse,
    RequirementCreate, RequirementUpdate, RequirementResponse,
    PaginatedRequirementResponse, RequirementFilter,
    AcceptanceCriteriaCreate, AcceptanceCriteriaUpdate, AcceptanceCriteriaResponse,
    RequirementCommentCreate, RequirementCommentResponse,
    RequirementTemplateCreate, RequirementTemplateResponse,
    RequirementExportFormat, RequirementAnalytics
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# Project Management Routes

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> ProjectResponse:
    """Create a new project."""
    try:
        project_service = ProjectService(db_session)

        project = await project_service.create_project(
            project_data=project_data,
            user_id=current_user.id,
            tenant_id=current_tenant.id
        )

        logger.info(
            "Created new project",
            project_id=project.id,
            user_id=current_user.id,
            tenant_id=current_tenant.id
        )

        return project

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error("Error creating project", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "PROJECT_CREATE_ERROR", "message": "Failed to create project"}
        )


@router.get("/projects", response_model=PaginatedProjectResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> PaginatedProjectResponse:
    """List projects accessible to the current user."""
    try:
        project_service = ProjectService(db_session)

        projects, total = await project_service.get_user_projects(
            user_id=current_user.id,
            tenant_id=current_tenant.id,
            page=page,
            page_size=page_size
        )

        # Convert to list items
        items = []
        for project in projects:
            items.append({
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "methodology": project.methodology,
                "is_active": project.is_active,
                "is_template": project.is_template,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "requirement_count": len(project.requirements) if hasattr(project, 'requirements') else 0,
                "member_count": len(project.members) if hasattr(project, 'members') else 0
            })

        pages = (total + page_size - 1) // page_size

        return PaginatedProjectResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error("Error listing projects", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "PROJECT_LIST_ERROR", "message": "Failed to list projects"}
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> ProjectResponse:
    """Get a specific project by ID."""
    try:
        project_service = ProjectService(db_session)
        project = await project_service.get_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PROJECT_NOT_FOUND", "message": "Project not found"}
            )

        # Check tenant access
        if project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to project"}
            )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            vision=project.vision,
            goals=project.goals or [],
            success_criteria=project.success_criteria or [],
            stakeholders=project.stakeholders or [],
            methodology=project.methodology,
            domain_model=project.domain_model or {},
            tenant_id=project.tenant_id,
            created_by=project.created_by,
            is_active=project.is_active,
            is_template=project.is_template,
            project_settings=project.project_settings or {},
            created_at=project.created_at,
            updated_at=project.updated_at,
            requirement_count=len(project.requirements) if hasattr(project, 'requirements') else 0,
            member_count=len(project.members) if hasattr(project, 'members') else 0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting project", error=str(e), project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "PROJECT_GET_ERROR", "message": "Failed to get project"}
        )


# Requirements Management Routes

@router.post("/projects/{project_id}/requirements", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    project_id: uuid.UUID,
    requirement_data: RequirementCreate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> RequirementResponse:
    """Create a new requirement in a project."""
    try:
        # Verify project exists and user has access
        project_service = ProjectService(db_session)
        project = await project_service.get_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PROJECT_NOT_FOUND", "message": "Project not found"}
            )

        if project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to project"}
            )

        requirement_service = RequirementService(db_session)
        requirement = await requirement_service.create_requirement(
            project_id=project_id,
            requirement_data=requirement_data,
            user_id=current_user.id
        )

        logger.info(
            "Created new requirement",
            requirement_id=requirement.id,
            project_id=project_id,
            user_id=current_user.id
        )

        return requirement

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating requirement", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REQUIREMENT_CREATE_ERROR", "message": "Failed to create requirement"}
        )


@router.get("/projects/{project_id}/requirements", response_model=PaginatedRequirementResponse)
async def list_requirements(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    requirement_type: Optional[str] = Query(None, description="Filter by requirement type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> PaginatedRequirementResponse:
    """List requirements in a project."""
    try:
        # Verify project access
        project_service = ProjectService(db_session)
        project = await project_service.get_project(project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PROJECT_NOT_FOUND", "message": "Project not found"}
            )

        # Build filters
        filters = RequirementFilter(
            requirement_type=requirement_type,
            status=status,
            priority=priority,
            search_query=search
        )

        requirement_service = RequirementService(db_session)
        requirements = await requirement_service.get_project_requirements(
            project_id=project_id,
            filters=filters,
            page=page,
            page_size=page_size
        )

        return requirements

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing requirements", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REQUIREMENT_LIST_ERROR", "message": "Failed to list requirements"}
        )


@router.get("/requirements/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> RequirementResponse:
    """Get a specific requirement by ID."""
    try:
        requirement_service = RequirementService(db_session)
        requirement = await requirement_service.get_requirement(requirement_id)

        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found"}
            )

        # Verify project access through project service
        project_service = ProjectService(db_session)
        project = await project_service.get_project(requirement.project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to requirement"}
            )

        return requirement

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting requirement", error=str(e), requirement_id=requirement_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REQUIREMENT_GET_ERROR", "message": "Failed to get requirement"}
        )


@router.put("/requirements/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: uuid.UUID,
    update_data: RequirementUpdate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> RequirementResponse:
    """Update a requirement."""
    try:
        requirement_service = RequirementService(db_session)

        # Verify access first
        existing_requirement = await requirement_service.get_requirement(requirement_id)
        if not existing_requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found"}
            )

        project_service = ProjectService(db_session)
        project = await project_service.get_project(existing_requirement.project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to requirement"}
            )

        requirement = await requirement_service.update_requirement(
            requirement_id=requirement_id,
            update_data=update_data,
            user_id=current_user.id
        )

        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found"}
            )

        logger.info(
            "Updated requirement",
            requirement_id=requirement_id,
            user_id=current_user.id
        )

        return requirement

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating requirement", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REQUIREMENT_UPDATE_ERROR", "message": "Failed to update requirement"}
        )


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> None:
    """Delete a requirement."""
    try:
        requirement_service = RequirementService(db_session)

        # Verify access first
        existing_requirement = await requirement_service.get_requirement(requirement_id)
        if not existing_requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found"}
            )

        project_service = ProjectService(db_session)
        project = await project_service.get_project(existing_requirement.project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to requirement"}
            )

        success = await requirement_service.delete_requirement(requirement_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found"}
            )

        logger.info("Deleted requirement", requirement_id=requirement_id, user_id=current_user.id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting requirement", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REQUIREMENT_DELETE_ERROR", "message": "Failed to delete requirement"}
        )


# Acceptance Criteria Routes

@router.post("/requirements/{requirement_id}/acceptance-criteria", response_model=AcceptanceCriteriaResponse, status_code=status.HTTP_201_CREATED)
async def create_acceptance_criteria(
    requirement_id: uuid.UUID,
    criteria_data: AcceptanceCriteriaCreate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> AcceptanceCriteriaResponse:
    """Create acceptance criteria for a requirement."""
    try:
        # Verify requirement access
        requirement_service = RequirementService(db_session)
        requirement = await requirement_service.get_requirement(requirement_id)

        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found"}
            )

        project_service = ProjectService(db_session)
        project = await project_service.get_project(requirement.project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to requirement"}
            )

        criteria = await requirement_service.create_acceptance_criteria(
            requirement_id=requirement_id,
            criteria_data=criteria_data,
            user_id=current_user.id
        )

        return AcceptanceCriteriaResponse(
            id=criteria.id,
            requirement_id=criteria.requirement_id,
            title=criteria.title,
            description=criteria.description,
            given_when_then=criteria.given_when_then,
            order_index=criteria.order_index,
            is_testable=criteria.is_testable,
            test_status=criteria.test_status,
            test_notes=criteria.test_notes,
            created_at=criteria.created_at,
            updated_at=criteria.updated_at,
            created_by=criteria.created_by
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating acceptance criteria", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ACCEPTANCE_CRITERIA_CREATE_ERROR", "message": "Failed to create acceptance criteria"}
        )


# Domain Analysis Routes

@router.get("/projects/{project_id}/domain/contexts")
async def get_bounded_contexts(
    project_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> List[str]:
    """Get all bounded contexts used in a project."""
    try:
        # Verify project access
        project_service = ProjectService(db_session)
        project = await project_service.get_project(project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PROJECT_NOT_FOUND", "message": "Project not found"}
            )

        domain_service = DomainService(db_session)
        contexts = await domain_service.get_bounded_contexts(project_id)

        return contexts

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting bounded contexts", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DOMAIN_ANALYSIS_ERROR", "message": "Failed to get bounded contexts"}
        )


@router.get("/projects/{project_id}/domain/analysis")
async def analyze_domain_model(
    project_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Analyze and return domain model structure for a project."""
    try:
        # Verify project access
        project_service = ProjectService(db_session)
        project = await project_service.get_project(project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PROJECT_NOT_FOUND", "message": "Project not found"}
            )

        domain_service = DomainService(db_session)
        domain_model = await domain_service.analyze_domain_model(project_id)

        return domain_model

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error analyzing domain model", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DOMAIN_ANALYSIS_ERROR", "message": "Failed to analyze domain model"}
        )


# Documentation Generation Routes

@router.post("/projects/{project_id}/documentation/generate")
async def generate_project_documentation(
    project_id: uuid.UUID,
    format_config: RequirementExportFormat,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> Response:
    """Generate project documentation in specified format."""
    try:
        # Verify project access
        project_service = ProjectService(db_session)
        project = await project_service.get_project(project_id)

        if not project or project.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PROJECT_NOT_FOUND", "message": "Project not found"}
            )

        if format_config.format_type == "markdown":
            requirement_service = RequirementService(db_session)
            domain_service = DomainService(db_session)

            generator = MarkdownGenerator(requirement_service, domain_service)

            content = await generator.generate_project_documentation(
                project=project,
                include_domain_model=True,
                include_acceptance_criteria=format_config.include_acceptance_criteria,
                include_comments=format_config.include_comments,
                template_name="default"
            )

            filename = f"{project.name.replace(' ', '_')}_requirements.md"

            return Response(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "UNSUPPORTED_FORMAT", "message": f"Format {format_config.format_type} not supported"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating documentation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DOCUMENTATION_GENERATION_ERROR", "message": "Failed to generate documentation"}
        )


# Health check for requirements service
@router.get("/health")
async def requirements_health_check() -> Dict[str, str]:
    """Health check for requirements service."""
    return {"status": "healthy", "service": "requirements"}
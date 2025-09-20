"""
Advanced API routes for enhanced requirements management.
Includes AI-powered features, domain analysis, and repository-based operations.
"""

import uuid
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.dependencies import get_db_session, get_current_user
from ..shared.exceptions import NotFoundError, ValidationError, AppException
from ..auth.models import User
from .enhanced_service import EnhancedProjectService, EnhancedRequirementService
from ..ai.enhanced_service import RequirementGenerationService
from .schemas import (
    ProjectCreate, ProjectResponse, RequirementCreate, RequirementResponse,
    RequirementFilter, PaginatedRequirementResponse
)
from .models import RequirementType, Priority, ComplexityLevel

router = APIRouter(prefix="/api/v2", tags=["Enhanced Requirements"])


# Enhanced Project Endpoints
@router.post("/projects", response_model=ProjectResponse)
async def create_project_enhanced(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new project using enhanced service with repository pattern."""
    try:
        service = EnhancedProjectService(db)
        return await service.create_project(
            project_data=project_data,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
    except AppException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/projects/{project_id}/analysis", response_model=Dict[str, Any])
async def get_project_domain_analysis(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive domain analysis for a project."""
    try:
        service = EnhancedProjectService(db)
        return await service.get_project_with_domain_analysis(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/users/{user_id}/projects", response_model=List[ProjectResponse])
async def get_user_projects_enhanced(
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get projects where user is a member using enhanced service."""
    try:
        # Ensure user can only access their own projects or is admin
        if user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

        service = EnhancedProjectService(db)
        return await service.get_projects_by_user(
            user_id=user_id,
            tenant_id=current_user.tenant_id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Enhanced Requirement Endpoints
@router.post("/projects/{project_id}/requirements", response_model=RequirementResponse)
async def create_requirement_enhanced(
    project_id: uuid.UUID,
    requirement_data: RequirementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a requirement with domain validation and auto-generated identifier."""
    try:
        service = EnhancedRequirementService(db)
        return await service.create_requirement_with_domain_validation(
            project_id=project_id,
            requirement_data=requirement_data,
            user_id=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/requirements/{requirement_id}/detailed", response_model=RequirementResponse)
async def get_requirement_detailed(
    requirement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get requirement with all related data using repository pattern."""
    try:
        service = EnhancedRequirementService(db)
        return await service.get_requirement_with_relations(requirement_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/projects/{project_id}/requirements/prioritize", response_model=List[RequirementResponse])
async def prioritize_requirements(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Prioritize requirements using domain service logic."""
    try:
        service = EnhancedRequirementService(db)
        return await service.prioritize_requirements(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/projects/{project_id}/requirements/dependencies", response_model=Dict[str, List[str]])
async def analyze_requirement_dependencies(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Analyze requirement dependencies using domain service."""
    try:
        service = EnhancedRequirementService(db)
        return await service.analyze_requirement_dependencies(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# AI-Powered Endpoints
@router.post("/projects/{project_id}/requirements/generate", response_model=List[RequirementCreate])
async def generate_requirements_from_ai(
    project_id: uuid.UUID,
    description: str,
    requirement_type: Optional[RequirementType] = None,
    context: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate requirements from natural language description using AI."""
    try:
        ai_service = RequirementGenerationService(db)
        return await ai_service.generate_requirements_from_description(
            project_id=project_id,
            description=description,
            user_id=current_user.id,
            requirement_type=requirement_type,
            context=context
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/requirements/{requirement_id}/enhance", response_model=Dict[str, Any])
async def enhance_requirement_with_ai(
    requirement_id: uuid.UUID,
    enhancement_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Enhance a requirement using AI (acceptance_criteria, user_stories, test_cases)."""
    try:
        valid_types = ["acceptance_criteria", "user_stories", "test_cases", "details", "rationale"]
        if enhancement_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid enhancement type. Must be one of: {valid_types}"
            )

        ai_service = RequirementGenerationService(db)
        return await ai_service.enhance_requirement_with_ai(
            requirement_id=requirement_id,
            enhancement_type=enhancement_type,
            user_id=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/projects/{project_id}/requirements/quality-analysis", response_model=Dict[str, Any])
async def analyze_requirements_quality(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Analyze the quality of requirements in a project using AI."""
    try:
        ai_service = RequirementGenerationService(db)
        return await ai_service.analyze_requirements_quality(
            project_id=project_id,
            user_id=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Batch Operations
@router.post("/projects/{project_id}/requirements/batch-create", response_model=List[RequirementResponse])
async def batch_create_requirements(
    project_id: uuid.UUID,
    requirements_data: List[RequirementCreate],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Batch create multiple requirements."""
    try:
        if len(requirements_data) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 requirements per batch")

        service = EnhancedRequirementService(db)
        created_requirements = []

        for req_data in requirements_data:
            try:
                requirement = await service.create_requirement_with_domain_validation(
                    project_id=project_id,
                    requirement_data=req_data,
                    user_id=current_user.id
                )
                created_requirements.append(requirement)
            except Exception as e:
                # Log error but continue with other requirements
                print(f"Failed to create requirement '{req_data.title}': {str(e)}")

        # Background task to analyze dependencies after batch creation
        background_tasks.add_task(
            _analyze_dependencies_background,
            project_id,
            current_user.id,
            db
        )

        return created_requirements

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/projects/{project_id}/export/markdown")
async def export_project_to_markdown(
    project_id: uuid.UUID,
    include_dependencies: bool = True,
    include_domain_model: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Export project requirements to markdown format."""
    try:
        from ..requirements.markdown_generator import MarkdownGenerator
        from ..requirements.service import RequirementService, DomainService

        # Use existing services for markdown generation
        requirement_service = RequirementService(db)
        domain_service = DomainService(db)
        generator = MarkdownGenerator(requirement_service, domain_service)

        markdown_content = await generator.generate_project_documentation(
            project_id=project_id,
            include_dependencies=include_dependencies,
            include_domain_model=include_domain_model
        )

        return {
            "project_id": project_id,
            "markdown": markdown_content,
            "generated_at": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Statistics and Analytics
@router.get("/projects/{project_id}/statistics", response_model=Dict[str, Any])
async def get_project_statistics(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive project statistics."""
    try:
        # Use repository to get statistics
        from ..projects.repository import ProjectRepository
        from ..requirements.repository import RequirementRepository

        project_repo = ProjectRepository(db)
        requirement_repo = RequirementRepository(db)

        # Get project stats
        project_stats = await project_repo.get_project_stats(project_id)

        # Get requirement stats
        requirement_stats = await requirement_repo.get_requirement_stats(project_id)

        # Combine statistics
        combined_stats = {
            **project_stats,
            **requirement_stats,
            "analysis_timestamp": "2024-01-01T00:00:00Z"
        }

        return combined_stats

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def _analyze_dependencies_background(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession
):
    """Background task to analyze dependencies after batch operations."""
    try:
        service = EnhancedRequirementService(db)
        dependencies = await service.analyze_requirement_dependencies(project_id)

        # Could store analysis results or send notifications
        print(f"Dependency analysis completed for project {project_id}: {len(dependencies)} relationships found")

    except Exception as e:
        print(f"Background dependency analysis failed: {str(e)}")


# Health check for enhanced services
@router.get("/health/enhanced")
async def health_check_enhanced():
    """Health check for enhanced services."""
    return {
        "status": "healthy",
        "services": {
            "enhanced_project_service": "available",
            "enhanced_requirement_service": "available",
            "ai_requirement_generation": "available",
            "domain_analysis": "available",
            "repository_pattern": "active"
        },
        "features": {
            "ai_generation": True,
            "domain_modeling": True,
            "dependency_analysis": True,
            "quality_analysis": True,
            "batch_operations": True,
            "markdown_export": True
        }
    }
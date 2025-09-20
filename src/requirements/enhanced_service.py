"""
Enhanced Requirements service with Repository pattern and Domain-driven design integration.
This service layer orchestrates repositories and domain services for complex business operations.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.exceptions import ValidationError, NotFoundError, AppException
from ..domain import RequirementDomainService, ProjectDomainService
from ..domain.models.value_objects import (
    Priority, PriorityLevel, ComplexityLevel, ComplexityScale,
    BusinessValue, StoryPoints, RequirementIdentifier
)
from .repository import RequirementRepository, AcceptanceCriteriaRepository, RequirementTemplateRepository
from ..projects.repository import ProjectRepository, ProjectMemberRepository
from .models import (
    Project, ProjectMember, Requirement, AcceptanceCriteria,
    RequirementComment, RequirementAttachment, RequirementTemplate,
    RequirementType, RequirementStatus
)
from .schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    RequirementCreate, RequirementUpdate, RequirementResponse,
    AcceptanceCriteriaCreate, AcceptanceCriteriaUpdate,
    RequirementFilter, PaginatedRequirementResponse
)

logger = structlog.get_logger(__name__)


class EnhancedProjectService:
    """Enhanced project service using repository pattern and domain services."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.project_repo = ProjectRepository(db_session)
        self.member_repo = ProjectMemberRepository(db_session)
        self.requirement_repo = RequirementRepository(db_session)
        self.project_domain_service = ProjectDomainService()

    async def create_project(
        self,
        project_data: ProjectCreate,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> ProjectResponse:
        """Create a new project using repository pattern."""
        try:
            # Create project instance
            project = Project(
                name=project_data.name,
                description=project_data.description,
                vision=project_data.vision,
                goals=project_data.goals or [],
                success_criteria=project_data.success_criteria or [],
                stakeholders=project_data.stakeholders or [],
                methodology=project_data.methodology,
                domain_model=project_data.domain_model or {},
                project_settings=project_data.project_settings or {},
                is_template=project_data.is_template,
                tenant_id=tenant_id,
                created_by=user_id
            )

            # Use repository to create project
            created_project = await self.project_repo.create(project)

            # Add creator as project owner using repository
            project_member = ProjectMember(
                project_id=created_project.id,
                user_id=user_id,
                role="owner",
                permissions={"all": True}
            )
            await self.member_repo.add_member(project_member)

            # Commit transaction
            await self.db_session.commit()

            logger.info(
                "Created new project with repository pattern",
                project_id=created_project.id,
                user_id=user_id,
                tenant_id=tenant_id,
                name=created_project.name
            )

            return self._project_to_response(created_project)

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Error creating project", error=str(e))
            raise AppException(f"Failed to create project: {str(e)}")

    async def get_project_with_domain_analysis(
        self,
        project_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get project with comprehensive domain analysis."""
        try:
            # Get project with members using repository
            project = await self.project_repo.get_by_id_with_members(project_id)
            if not project:
                raise NotFoundError("Project", str(project_id))

            # Get all requirements for domain analysis
            requirements = await self.requirement_repo.get_by_project(project_id)

            # Convert to format for domain service
            requirements_data = [self._requirement_to_domain_data(req) for req in requirements]

            # Perform domain analysis using domain service
            domain_analysis = await self.project_domain_service.analyze_domain_model(requirements_data)

            # Get project statistics
            project_stats = await self.project_repo.get_project_stats(project_id)

            return {
                "project": self._project_to_response(project),
                "domain_analysis": domain_analysis,
                "statistics": project_stats,
                "member_count": len(project.members)
            }

        except Exception as e:
            logger.error("Error getting project with domain analysis", project_id=str(project_id), error=str(e))
            raise AppException(f"Failed to get project analysis: {str(e)}")

    async def get_projects_by_user(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProjectResponse]:
        """Get projects where user is a member using repository."""
        try:
            projects = await self.project_repo.get_by_user(user_id, tenant_id, skip, limit)
            return [self._project_to_response(project) for project in projects]

        except Exception as e:
            logger.error("Error getting user projects", user_id=str(user_id), error=str(e))
            raise AppException(f"Failed to get user projects: {str(e)}")

    def _project_to_response(self, project: Project) -> ProjectResponse:
        """Convert project model to response schema."""
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
            updated_at=project.updated_at
        )

    def _requirement_to_domain_data(self, requirement: Requirement) -> Dict[str, Any]:
        """Convert requirement model to domain service format."""
        return {
            "id": str(requirement.id),
            "title": requirement.title,
            "description": requirement.description,
            "requirement_type": requirement.requirement_type.value if requirement.requirement_type else None,
            "priority": requirement.priority.value if requirement.priority else None,
            "complexity": requirement.complexity.value if requirement.complexity else 1,
            "story_points": requirement.story_points or 1,
            "business_value": requirement.business_value or 50,
            "bounded_context": requirement.bounded_context,
            "domain_entity": requirement.domain_entity,
            "aggregate_root": requirement.aggregate_root,
            "depends_on": requirement.depends_on or [],
            "related_requirements": requirement.related_requirements or []
        }


class EnhancedRequirementService:
    """Enhanced requirement service using repository pattern and domain services."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.requirement_repo = RequirementRepository(db_session)
        self.criteria_repo = AcceptanceCriteriaRepository(db_session)
        self.template_repo = RequirementTemplateRepository(db_session)
        self.project_repo = ProjectRepository(db_session)
        self.requirement_domain_service = RequirementDomainService()

    async def create_requirement_with_domain_validation(
        self,
        project_id: uuid.UUID,
        requirement_data: RequirementCreate,
        user_id: uuid.UUID
    ) -> RequirementResponse:
        """Create requirement with domain-driven validation and identifier generation."""
        try:
            # Validate project exists
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                raise NotFoundError("Project", str(project_id))

            # Generate next identifier using repository
            next_number = await self.requirement_repo.get_next_identifier_number(
                project_id,
                requirement_data.identifier_prefix or "REQ"
            )

            # Create domain value object for identifier
            identifier = RequirementIdentifier(
                prefix=requirement_data.identifier_prefix or "REQ",
                number=next_number
            )

            # Create domain value objects
            priority = Priority(
                level=PriorityLevel(requirement_data.priority.value),
                reason=getattr(requirement_data, 'priority_reason', None)
            )

            complexity = ComplexityLevel(
                scale=ComplexityScale(requirement_data.complexity.value),
                explanation=getattr(requirement_data, 'complexity_explanation', None)
            )

            business_value = BusinessValue(
                score=requirement_data.business_value or 50,
                justification=getattr(requirement_data, 'business_value_justification', None)
            )

            story_points = StoryPoints(
                points=requirement_data.story_points or 1,
                estimation_method=getattr(requirement_data, 'estimation_method', None)
            )

            # Create requirement instance
            requirement = Requirement(
                identifier=identifier.full_identifier,
                title=requirement_data.title,
                description=requirement_data.description,
                rationale=requirement_data.rationale,
                requirement_type=requirement_data.requirement_type,
                category=requirement_data.category,
                tags=requirement_data.tags or [],
                priority=requirement_data.priority,
                complexity=requirement_data.complexity,
                user_persona=requirement_data.user_persona,
                user_goal=requirement_data.user_goal,
                user_benefit=requirement_data.user_benefit,
                story_points=story_points.points,
                estimated_hours=requirement_data.estimated_hours,
                business_value=business_value.score,
                depends_on=requirement_data.depends_on or [],
                related_requirements=requirement_data.related_requirements or [],
                bounded_context=requirement_data.bounded_context,
                domain_entity=requirement_data.domain_entity,
                aggregate_root=requirement_data.aggregate_root,
                custom_fields=requirement_data.custom_fields or {},
                source=requirement_data.source,
                ai_generated=requirement_data.ai_generated,
                project_id=project_id,
                created_by=user_id,
                status=RequirementStatus.DRAFT
            )

            # Use repository to create requirement
            created_requirement = await self.requirement_repo.create(requirement)

            # Create acceptance criteria if provided
            if requirement_data.acceptance_criteria:
                for order, criteria_text in enumerate(requirement_data.acceptance_criteria):
                    criteria = AcceptanceCriteria(
                        requirement_id=created_requirement.id,
                        description=criteria_text,
                        order=order + 1,
                        created_by=user_id
                    )
                    await self.criteria_repo.create(criteria)

            # Commit transaction
            await self.db_session.commit()

            logger.info(
                "Created requirement with domain validation",
                requirement_id=created_requirement.id,
                identifier=created_requirement.identifier,
                project_id=project_id
            )

            return await self._requirement_to_response(created_requirement)

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Error creating requirement", error=str(e))
            raise AppException(f"Failed to create requirement: {str(e)}")

    async def prioritize_requirements(
        self,
        project_id: uuid.UUID
    ) -> List[RequirementResponse]:
        """Prioritize requirements using domain service logic."""
        try:
            # Get all requirements using repository
            requirements = await self.requirement_repo.get_by_project(project_id)

            # Convert to domain service format
            requirements_data = [self._requirement_to_domain_data(req) for req in requirements]

            # Use domain service to prioritize
            prioritized_data = self.requirement_domain_service.prioritize_requirements(requirements_data)

            # Find corresponding requirement objects in prioritized order
            prioritized_requirements = []
            for req_data in prioritized_data:
                for req in requirements:
                    if str(req.id) == req_data['id']:
                        prioritized_requirements.append(req)
                        break

            return [await self._requirement_to_response(req) for req in prioritized_requirements]

        except Exception as e:
            logger.error("Error prioritizing requirements", project_id=str(project_id), error=str(e))
            raise AppException(f"Failed to prioritize requirements: {str(e)}")

    async def analyze_requirement_dependencies(
        self,
        project_id: uuid.UUID
    ) -> Dict[str, List[str]]:
        """Analyze requirement dependencies using domain service."""
        try:
            # Get all requirements using repository
            requirements = await self.requirement_repo.get_by_project(project_id)

            # Convert to domain service format
            requirements_data = [self._requirement_to_domain_data(req) for req in requirements]

            # Use domain service to identify dependencies
            dependencies = self.requirement_domain_service.identify_requirement_dependencies(requirements_data)

            return dependencies

        except Exception as e:
            logger.error("Error analyzing dependencies", project_id=str(project_id), error=str(e))
            raise AppException(f"Failed to analyze dependencies: {str(e)}")

    async def get_requirement_with_relations(
        self,
        requirement_id: uuid.UUID
    ) -> RequirementResponse:
        """Get requirement with all related data using repository."""
        try:
            requirement = await self.requirement_repo.get_by_id_with_relations(requirement_id)
            if not requirement:
                raise NotFoundError("Requirement", str(requirement_id))

            return await self._requirement_to_response(requirement)

        except Exception as e:
            logger.error("Error getting requirement", requirement_id=str(requirement_id), error=str(e))
            raise AppException(f"Failed to get requirement: {str(e)}")

    def _requirement_to_domain_data(self, requirement: Requirement) -> Dict[str, Any]:
        """Convert requirement model to domain service format."""
        return {
            "id": str(requirement.id),
            "title": requirement.title,
            "description": requirement.description,
            "requirement_type": requirement.requirement_type.value if requirement.requirement_type else None,
            "priority": requirement.priority.value if requirement.priority else None,
            "complexity": requirement.complexity.value if requirement.complexity else 1,
            "story_points": requirement.story_points or 1,
            "business_value": requirement.business_value or 50,
            "bounded_context": requirement.bounded_context,
            "domain_entity": requirement.domain_entity,
            "aggregate_root": requirement.aggregate_root,
            "depends_on": requirement.depends_on or [],
            "related_requirements": requirement.related_requirements or [],
            "domain_entities": [requirement.domain_entity] if requirement.domain_entity else []
        }

    async def _requirement_to_response(self, requirement: Requirement) -> RequirementResponse:
        """Convert requirement model to response schema."""
        # Get acceptance criteria if not loaded
        if not hasattr(requirement, 'acceptance_criteria') or requirement.acceptance_criteria is None:
            criteria = await self.criteria_repo.get_by_requirement(requirement.id)
            acceptance_criteria = [c.description for c in criteria]
        else:
            acceptance_criteria = [c.description for c in requirement.acceptance_criteria]

        return RequirementResponse(
            id=requirement.id,
            identifier=requirement.identifier,
            title=requirement.title,
            description=requirement.description,
            rationale=requirement.rationale,
            requirement_type=requirement.requirement_type,
            category=requirement.category,
            tags=requirement.tags or [],
            priority=requirement.priority,
            complexity=requirement.complexity,
            status=requirement.status,
            user_persona=requirement.user_persona,
            user_goal=requirement.user_goal,
            user_benefit=requirement.user_benefit,
            story_points=requirement.story_points,
            estimated_hours=requirement.estimated_hours,
            business_value=requirement.business_value,
            depends_on=requirement.depends_on or [],
            related_requirements=requirement.related_requirements or [],
            acceptance_criteria=acceptance_criteria,
            bounded_context=requirement.bounded_context,
            domain_entity=requirement.domain_entity,
            aggregate_root=requirement.aggregate_root,
            custom_fields=requirement.custom_fields or {},
            source=requirement.source,
            ai_generated=requirement.ai_generated,
            project_id=requirement.project_id,
            created_by=requirement.created_by,
            updated_by=requirement.updated_by,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )
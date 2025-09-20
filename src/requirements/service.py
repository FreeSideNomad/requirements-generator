"""
Requirements domain service for business logic and operations.
Handles projects, requirements, acceptance criteria, and domain-driven design features.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import structlog
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..shared.exceptions import ValidationError, NotFoundError, AppException
from ..ai.service import ConversationService
from .models import (
    Project, ProjectMember, Requirement, AcceptanceCriteria,
    RequirementComment, RequirementAttachment, RequirementTemplate,
    RequirementType, RequirementStatus, Priority
)
from .schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    RequirementCreate, RequirementUpdate, RequirementResponse,
    AcceptanceCriteriaCreate, AcceptanceCriteriaUpdate,
    RequirementFilter, PaginatedRequirementResponse
)

logger = structlog.get_logger(__name__)


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_project(
        self,
        project_data: ProjectCreate,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> ProjectResponse:
        """Create a new project."""
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

            self.db_session.add(project)
            await self.db_session.flush()

            # Add creator as project owner
            project_member = ProjectMember(
                project_id=project.id,
                user_id=user_id,
                role="owner",
                permissions={"all": True}
            )

            self.db_session.add(project_member)
            await self.db_session.commit()

            logger.info(
                "Created new project",
                project_id=project.id,
                user_id=user_id,
                tenant_id=tenant_id,
                name=project.name
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
                requirement_count=0,
                member_count=1
            )

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Error creating project", error=str(e))
            raise AppException(
                message="Failed to create project",
                error_code="PROJECT_CREATE_ERROR",
                status_code=500
            )

    async def get_project(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID."""
        try:
            result = await self.db_session.execute(
                select(Project)
                .options(selectinload(Project.requirements))
                .options(selectinload(Project.members))
                .where(Project.id == project_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("Error getting project", error=str(e), project_id=project_id)
            return None

    async def get_user_projects(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Project], int]:
        """Get projects accessible to user."""
        try:
            # Get projects where user is a member
            offset = (page - 1) * page_size

            query = (
                select(Project)
                .join(ProjectMember)
                .where(
                    and_(
                        Project.tenant_id == tenant_id,
                        ProjectMember.user_id == user_id,
                        ProjectMember.is_active == True
                    )
                )
                .order_by(Project.updated_at.desc())
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db_session.execute(query)
            projects = result.scalars().all()

            # Get total count
            count_query = (
                select(func.count(Project.id))
                .join(ProjectMember)
                .where(
                    and_(
                        Project.tenant_id == tenant_id,
                        ProjectMember.user_id == user_id,
                        ProjectMember.is_active == True
                    )
                )
            )
            count_result = await self.db_session.execute(count_query)
            total = count_result.scalar()

            return projects, total

        except Exception as e:
            logger.error("Error getting user projects", error=str(e), user_id=user_id)
            return [], 0


class RequirementService:
    """Service for requirement management operations."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.conversation_service = ConversationService(db_session)

    async def create_requirement(
        self,
        project_id: uuid.UUID,
        requirement_data: RequirementCreate,
        user_id: uuid.UUID
    ) -> RequirementResponse:
        """Create a new requirement."""
        try:
            # Generate identifier if not provided
            identifier = await self._generate_identifier(
                project_id,
                requirement_data.requirement_type
            )

            # Create requirement instance
            requirement = Requirement(
                project_id=project_id,
                parent_id=requirement_data.parent_id,
                order_index=requirement_data.order_index,
                identifier=identifier,
                title=requirement_data.title,
                description=requirement_data.description,
                rationale=requirement_data.rationale,
                requirement_type=requirement_data.requirement_type,
                category=requirement_data.category,
                tags=requirement_data.tags or [],
                status=RequirementStatus.DRAFT,
                priority=requirement_data.priority,
                complexity=requirement_data.complexity,
                user_persona=requirement_data.user_persona,
                user_goal=requirement_data.user_goal,
                user_benefit=requirement_data.user_benefit,
                story_points=requirement_data.story_points,
                estimated_hours=requirement_data.estimated_hours,
                business_value=requirement_data.business_value,
                depends_on=requirement_data.depends_on or [],
                related_requirements=requirement_data.related_requirements or [],
                bounded_context=requirement_data.bounded_context,
                domain_entity=requirement_data.domain_entity,
                aggregate_root=requirement_data.aggregate_root,
                ai_generated=requirement_data.ai_generated,
                ai_conversation_id=requirement_data.ai_conversation_id,
                generation_prompt=requirement_data.generation_prompt,
                custom_fields=requirement_data.custom_fields or {},
                source=requirement_data.source,
                created_by=user_id
            )

            self.db_session.add(requirement)
            await self.db_session.flush()

            logger.info(
                "Created new requirement",
                requirement_id=requirement.id,
                project_id=project_id,
                identifier=identifier,
                requirement_type=requirement_data.requirement_type
            )

            return await self._requirement_to_response(requirement)

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Error creating requirement", error=str(e))
            raise AppException(
                message="Failed to create requirement",
                error_code="REQUIREMENT_CREATE_ERROR",
                status_code=500
            )

    async def get_requirement(self, requirement_id: uuid.UUID) -> Optional[RequirementResponse]:
        """Get requirement by ID."""
        try:
            result = await self.db_session.execute(
                select(Requirement)
                .options(selectinload(Requirement.children))
                .options(selectinload(Requirement.acceptance_criteria))
                .where(Requirement.id == requirement_id)
            )
            requirement = result.scalar_one_or_none()

            if requirement:
                return await self._requirement_to_response(requirement)
            return None

        except Exception as e:
            logger.error("Error getting requirement", error=str(e), requirement_id=requirement_id)
            return None

    async def update_requirement(
        self,
        requirement_id: uuid.UUID,
        update_data: RequirementUpdate,
        user_id: uuid.UUID
    ) -> Optional[RequirementResponse]:
        """Update an existing requirement."""
        try:
            # Get existing requirement
            result = await self.db_session.execute(
                select(Requirement).where(Requirement.id == requirement_id)
            )
            requirement = result.scalar_one_or_none()

            if not requirement:
                return None

            # Create new version if significant changes
            should_version = self._should_create_version(requirement, update_data)
            if should_version:
                requirement.previous_version_id = requirement.id
                requirement.version += 1
                requirement.change_reason = update_data.change_reason

            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                if field != "change_reason" and hasattr(requirement, field):
                    setattr(requirement, field, value)

            requirement.updated_by = user_id
            requirement.updated_at = datetime.utcnow()

            await self.db_session.commit()

            logger.info(
                "Updated requirement",
                requirement_id=requirement_id,
                user_id=user_id,
                versioned=should_version
            )

            return await self._requirement_to_response(requirement)

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Error updating requirement", error=str(e))
            raise AppException(
                message="Failed to update requirement",
                error_code="REQUIREMENT_UPDATE_ERROR",
                status_code=500
            )

    async def delete_requirement(self, requirement_id: uuid.UUID) -> bool:
        """Delete a requirement."""
        try:
            result = await self.db_session.execute(
                select(Requirement).where(Requirement.id == requirement_id)
            )
            requirement = result.scalar_one_or_none()

            if not requirement:
                return False

            await self.db_session.delete(requirement)
            await self.db_session.commit()

            logger.info("Deleted requirement", requirement_id=requirement_id)
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Error deleting requirement", error=str(e))
            return False

    async def get_project_requirements(
        self,
        project_id: uuid.UUID,
        filters: Optional[RequirementFilter] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedRequirementResponse:
        """Get requirements for a project with filtering."""
        try:
            offset = (page - 1) * page_size

            # Build base query
            query = select(Requirement).where(Requirement.project_id == project_id)

            # Apply filters
            if filters:
                if filters.requirement_type:
                    query = query.where(Requirement.requirement_type == filters.requirement_type)
                if filters.status:
                    query = query.where(Requirement.status == filters.status)
                if filters.priority:
                    query = query.where(Requirement.priority == filters.priority)
                if filters.complexity:
                    query = query.where(Requirement.complexity == filters.complexity)
                if filters.search_query:
                    search_term = f"%{filters.search_query}%"
                    query = query.where(
                        or_(
                            Requirement.title.ilike(search_term),
                            Requirement.description.ilike(search_term)
                        )
                    )
                if filters.bounded_context:
                    query = query.where(Requirement.bounded_context == filters.bounded_context)
                if filters.created_by:
                    query = query.where(Requirement.created_by == filters.created_by)
                if filters.is_ai_generated is not None:
                    query = query.where(Requirement.ai_generated == filters.is_ai_generated)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.db_session.execute(count_query)
            total = count_result.scalar()

            # Get paginated results
            query = query.order_by(Requirement.order_index, Requirement.created_at).offset(offset).limit(page_size)
            result = await self.db_session.execute(query)
            requirements = result.scalars().all()

            # Convert to list items
            items = []
            for req in requirements:
                # Get counts
                children_count = len(req.children) if hasattr(req, 'children') else 0
                ac_count = len(req.acceptance_criteria) if hasattr(req, 'acceptance_criteria') else 0

                items.append({
                    "id": req.id,
                    "identifier": req.identifier,
                    "title": req.title,
                    "requirement_type": req.requirement_type,
                    "status": req.status,
                    "priority": req.priority,
                    "complexity": req.complexity,
                    "parent_id": req.parent_id,
                    "story_points": req.story_points,
                    "business_value": req.business_value,
                    "created_at": req.created_at,
                    "updated_at": req.updated_at,
                    "created_by": req.created_by,
                    "children_count": children_count,
                    "acceptance_criteria_count": ac_count
                })

            pages = (total + page_size - 1) // page_size

            return PaginatedRequirementResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
                has_next=page < pages,
                has_previous=page > 1
            )

        except Exception as e:
            logger.error("Error getting project requirements", error=str(e))
            raise AppException(
                message="Failed to get requirements",
                error_code="REQUIREMENT_LIST_ERROR",
                status_code=500
            )

    async def create_acceptance_criteria(
        self,
        requirement_id: uuid.UUID,
        criteria_data: AcceptanceCriteriaCreate,
        user_id: uuid.UUID
    ) -> AcceptanceCriteria:
        """Create acceptance criteria for a requirement."""
        try:
            criteria = AcceptanceCriteria(
                requirement_id=requirement_id,
                title=criteria_data.title,
                description=criteria_data.description,
                given_when_then=criteria_data.given_when_then,
                order_index=criteria_data.order_index,
                is_testable=criteria_data.is_testable,
                created_by=user_id
            )

            self.db_session.add(criteria)
            await self.db_session.commit()

            logger.info(
                "Created acceptance criteria",
                criteria_id=criteria.id,
                requirement_id=requirement_id
            )

            return criteria

        except Exception as e:
            await self.db_session.rollback()
            logger.error("Error creating acceptance criteria", error=str(e))
            raise AppException(
                message="Failed to create acceptance criteria",
                error_code="ACCEPTANCE_CRITERIA_CREATE_ERROR",
                status_code=500
            )

    async def _generate_identifier(self, project_id: uuid.UUID, requirement_type: RequirementType) -> str:
        """Generate unique identifier for requirement."""
        # Get prefix based on type
        type_prefixes = {
            RequirementType.EPIC: "EPIC",
            RequirementType.USER_STORY: "US",
            RequirementType.FUNCTIONAL: "FR",
            RequirementType.NON_FUNCTIONAL: "NFR",
            RequirementType.BUSINESS_RULE: "BR",
            RequirementType.CONSTRAINT: "CON",
            RequirementType.ASSUMPTION: "ASM"
        }

        prefix = type_prefixes.get(requirement_type, "REQ")

        # Get next number for this type in project
        result = await self.db_session.execute(
            select(func.count(Requirement.id))
            .where(
                and_(
                    Requirement.project_id == project_id,
                    Requirement.requirement_type == requirement_type
                )
            )
        )
        count = result.scalar() or 0

        return f"{prefix}-{count + 1:03d}"

    async def _requirement_to_response(self, requirement: Requirement) -> RequirementResponse:
        """Convert requirement model to response schema."""
        children_count = len(requirement.children) if hasattr(requirement, 'children') else 0
        ac_count = len(requirement.acceptance_criteria) if hasattr(requirement, 'acceptance_criteria') else 0

        return RequirementResponse(
            id=requirement.id,
            project_id=requirement.project_id,
            parent_id=requirement.parent_id,
            identifier=requirement.identifier,
            order_index=requirement.order_index,
            title=requirement.title,
            description=requirement.description,
            rationale=requirement.rationale,
            requirement_type=requirement.requirement_type,
            category=requirement.category,
            tags=requirement.tags or [],
            status=requirement.status,
            priority=requirement.priority,
            complexity=requirement.complexity,
            user_persona=requirement.user_persona,
            user_goal=requirement.user_goal,
            user_benefit=requirement.user_benefit,
            story_points=requirement.story_points,
            estimated_hours=requirement.estimated_hours,
            business_value=requirement.business_value,
            depends_on=requirement.depends_on or [],
            related_requirements=requirement.related_requirements or [],
            bounded_context=requirement.bounded_context,
            domain_entity=requirement.domain_entity,
            aggregate_root=requirement.aggregate_root,
            approved_by=requirement.approved_by,
            approved_at=requirement.approved_at,
            review_notes=requirement.review_notes,
            ai_generated=requirement.ai_generated,
            ai_conversation_id=requirement.ai_conversation_id,
            generation_prompt=requirement.generation_prompt,
            version=requirement.version,
            previous_version_id=requirement.previous_version_id,
            change_reason=requirement.change_reason,
            custom_fields=requirement.custom_fields or {},
            source=requirement.source,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at,
            created_by=requirement.created_by,
            updated_by=requirement.updated_by,
            children_count=children_count,
            acceptance_criteria_count=ac_count
        )

    def _should_create_version(self, requirement: Requirement, update_data: RequirementUpdate) -> bool:
        """Determine if requirement update should create a new version."""
        significant_fields = ['title', 'description', 'requirement_type', 'status']

        for field in significant_fields:
            if hasattr(update_data, field) and getattr(update_data, field) is not None:
                if getattr(requirement, field) != getattr(update_data, field):
                    return True

        return False


class DomainService:
    """Service for domain-driven design features."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_bounded_contexts(self, project_id: uuid.UUID) -> List[str]:
        """Get all bounded contexts used in a project."""
        try:
            result = await self.db_session.execute(
                select(Requirement.bounded_context)
                .where(
                    and_(
                        Requirement.project_id == project_id,
                        Requirement.bounded_context.isnot(None)
                    )
                )
                .distinct()
            )
            contexts = [row[0] for row in result.fetchall() if row[0]]
            return sorted(contexts)

        except Exception as e:
            logger.error("Error getting bounded contexts", error=str(e))
            return []

    async def get_domain_entities(self, project_id: uuid.UUID, bounded_context: Optional[str] = None) -> List[str]:
        """Get all domain entities in a project or bounded context."""
        try:
            query = select(Requirement.domain_entity).where(
                and_(
                    Requirement.project_id == project_id,
                    Requirement.domain_entity.isnot(None)
                )
            )

            if bounded_context:
                query = query.where(Requirement.bounded_context == bounded_context)

            result = await self.db_session.execute(query.distinct())
            entities = [row[0] for row in result.fetchall() if row[0]]
            return sorted(entities)

        except Exception as e:
            logger.error("Error getting domain entities", error=str(e))
            return []

    async def analyze_domain_model(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """Analyze and return domain model structure for a project."""
        try:
            # Get all requirements with domain information
            result = await self.db_session.execute(
                select(Requirement)
                .where(Requirement.project_id == project_id)
                .where(
                    or_(
                        Requirement.bounded_context.isnot(None),
                        Requirement.domain_entity.isnot(None),
                        Requirement.aggregate_root.isnot(None)
                    )
                )
            )
            requirements = result.scalars().all()

            # Organize by bounded context
            domain_model = {}
            for req in requirements:
                context = req.bounded_context or "Unspecified"
                if context not in domain_model:
                    domain_model[context] = {
                        "entities": set(),
                        "aggregates": set(),
                        "requirements": []
                    }

                if req.domain_entity:
                    domain_model[context]["entities"].add(req.domain_entity)
                if req.aggregate_root:
                    domain_model[context]["aggregates"].add(req.aggregate_root)

                domain_model[context]["requirements"].append({
                    "id": str(req.id),
                    "identifier": req.identifier,
                    "title": req.title,
                    "type": req.requirement_type,
                    "entity": req.domain_entity,
                    "aggregate": req.aggregate_root
                })

            # Convert sets to lists for JSON serialization
            for context in domain_model:
                domain_model[context]["entities"] = sorted(list(domain_model[context]["entities"]))
                domain_model[context]["aggregates"] = sorted(list(domain_model[context]["aggregates"]))

            return domain_model

        except Exception as e:
            logger.error("Error analyzing domain model", error=str(e))
            return {}
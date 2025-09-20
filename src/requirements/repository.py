"""
Repository layer for Requirements domain.
Handles data access and persistence operations for requirements.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import structlog

from ..shared.exceptions import NotFoundError, DatabaseError
from .models import (
    Requirement, AcceptanceCriteria, RequirementComment,
    RequirementAttachment, RequirementTemplate,
    RequirementType, RequirementStatus, Priority
)


logger = structlog.get_logger(__name__)


class RequirementRepository:
    """Repository for Requirement entity operations."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, requirement: Requirement) -> Requirement:
        """Create a new requirement."""
        try:
            self.db_session.add(requirement)
            await self.db_session.flush()
            await self.db_session.refresh(requirement)
            return requirement
        except Exception as e:
            logger.error("Error creating requirement", error=str(e))
            raise DatabaseError(f"Failed to create requirement: {str(e)}")

    async def get_by_id(self, requirement_id: uuid.UUID) -> Optional[Requirement]:
        """Get requirement by ID."""
        try:
            stmt = select(Requirement).where(Requirement.id == requirement_id)
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting requirement by ID", requirement_id=str(requirement_id), error=str(e))
            raise DatabaseError(f"Failed to get requirement: {str(e)}")

    async def get_by_id_with_relations(self, requirement_id: uuid.UUID) -> Optional[Requirement]:
        """Get requirement by ID with all related data loaded."""
        try:
            stmt = (
                select(Requirement)
                .options(
                    selectinload(Requirement.acceptance_criteria),
                    selectinload(Requirement.comments),
                    selectinload(Requirement.attachments)
                )
                .where(Requirement.id == requirement_id)
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting requirement with relations", requirement_id=str(requirement_id), error=str(e))
            raise DatabaseError(f"Failed to get requirement with relations: {str(e)}")

    async def get_by_project(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[RequirementStatus] = None,
        requirement_type: Optional[RequirementType] = None,
        priority: Optional[Priority] = None
    ) -> List[Requirement]:
        """Get requirements by project with optional filters."""
        try:
            conditions = [Requirement.project_id == project_id]

            if status:
                conditions.append(Requirement.status == status)
            if requirement_type:
                conditions.append(Requirement.requirement_type == requirement_type)
            if priority:
                conditions.append(Requirement.priority == priority)

            stmt = (
                select(Requirement)
                .where(and_(*conditions))
                .order_by(desc(Requirement.created_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting requirements by project", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to get requirements: {str(e)}")

    async def get_by_identifier(self, identifier: str, project_id: uuid.UUID) -> Optional[Requirement]:
        """Get requirement by identifier within a project."""
        try:
            stmt = select(Requirement).where(
                and_(
                    Requirement.identifier == identifier,
                    Requirement.project_id == project_id
                )
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting requirement by identifier", identifier=identifier, error=str(e))
            raise DatabaseError(f"Failed to get requirement by identifier: {str(e)}")

    async def update(self, requirement: Requirement) -> Requirement:
        """Update a requirement."""
        try:
            requirement.updated_at = datetime.utcnow()
            await self.db_session.flush()
            await self.db_session.refresh(requirement)
            return requirement
        except Exception as e:
            logger.error("Error updating requirement", requirement_id=str(requirement.id), error=str(e))
            raise DatabaseError(f"Failed to update requirement: {str(e)}")

    async def delete(self, requirement_id: uuid.UUID) -> bool:
        """Delete a requirement."""
        try:
            stmt = select(Requirement).where(Requirement.id == requirement_id)
            result = await self.db_session.execute(stmt)
            requirement = result.scalar_one_or_none()

            if not requirement:
                return False

            await self.db_session.delete(requirement)
            await self.db_session.flush()
            return True
        except Exception as e:
            logger.error("Error deleting requirement", requirement_id=str(requirement_id), error=str(e))
            raise DatabaseError(f"Failed to delete requirement: {str(e)}")

    async def search(
        self,
        project_id: uuid.UUID,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Requirement]:
        """Search requirements by title, description, or acceptance criteria."""
        try:
            search_term = f"%{query}%"
            stmt = (
                select(Requirement)
                .where(
                    and_(
                        Requirement.project_id == project_id,
                        or_(
                            Requirement.title.ilike(search_term),
                            Requirement.description.ilike(search_term),
                            Requirement.identifier.ilike(search_term),
                            Requirement.category.ilike(search_term)
                        )
                    )
                )
                .order_by(desc(Requirement.updated_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error searching requirements", query=query, error=str(e))
            raise DatabaseError(f"Failed to search requirements: {str(e)}")

    async def get_by_bounded_context(
        self,
        project_id: uuid.UUID,
        bounded_context: str
    ) -> List[Requirement]:
        """Get requirements by bounded context."""
        try:
            stmt = (
                select(Requirement)
                .where(
                    and_(
                        Requirement.project_id == project_id,
                        Requirement.bounded_context == bounded_context
                    )
                )
                .order_by(Requirement.identifier)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting requirements by bounded context", bounded_context=bounded_context, error=str(e))
            raise DatabaseError(f"Failed to get requirements by bounded context: {str(e)}")

    async def get_dependencies(self, requirement_id: uuid.UUID) -> List[Requirement]:
        """Get requirements that this requirement depends on."""
        try:
            requirement = await self.get_by_id(requirement_id)
            if not requirement or not requirement.depends_on:
                return []

            stmt = select(Requirement).where(
                and_(
                    Requirement.id.in_(requirement.depends_on),
                    Requirement.project_id == requirement.project_id
                )
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting requirement dependencies", requirement_id=str(requirement_id), error=str(e))
            raise DatabaseError(f"Failed to get requirement dependencies: {str(e)}")

    async def get_dependents(self, requirement_id: uuid.UUID) -> List[Requirement]:
        """Get requirements that depend on this requirement."""
        try:
            requirement = await self.get_by_id(requirement_id)
            if not requirement:
                return []

            # Use PostgreSQL's ANY operator for array search
            stmt = select(Requirement).where(
                and_(
                    Requirement.depends_on.any(requirement_id),
                    Requirement.project_id == requirement.project_id
                )
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting requirement dependents", requirement_id=str(requirement_id), error=str(e))
            raise DatabaseError(f"Failed to get requirement dependents: {str(e)}")

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        """Count requirements by project."""
        try:
            stmt = select(func.count(Requirement.id)).where(Requirement.project_id == project_id)
            result = await self.db_session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error("Error counting requirements", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to count requirements: {str(e)}")

    async def get_next_identifier_number(self, project_id: uuid.UUID, prefix: str) -> int:
        """Get the next identifier number for a given prefix."""
        try:
            stmt = (
                select(func.max(func.cast(
                    func.substring(Requirement.identifier, len(prefix) + 2), # +2 for the dash
                    'integer'
                )))
                .where(
                    and_(
                        Requirement.project_id == project_id,
                        Requirement.identifier.like(f"{prefix}-%")
                    )
                )
            )
            result = await self.db_session.execute(stmt)
            max_number = result.scalar()
            return (max_number or 0) + 1
        except Exception as e:
            logger.error("Error getting next identifier number", prefix=prefix, error=str(e))
            return 1  # Start from 1 if there's an error

    async def get_requirement_stats(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """Get requirement statistics for a project."""
        try:
            # Count by status
            status_counts_stmt = (
                select(
                    Requirement.status,
                    func.count(Requirement.id).label('count')
                )
                .where(Requirement.project_id == project_id)
                .group_by(Requirement.status)
            )
            status_result = await self.db_session.execute(status_counts_stmt)
            status_counts = {row.status.value: row.count for row in status_result}

            # Count by type
            type_counts_stmt = (
                select(
                    Requirement.requirement_type,
                    func.count(Requirement.id).label('count')
                )
                .where(Requirement.project_id == project_id)
                .group_by(Requirement.requirement_type)
            )
            type_result = await self.db_session.execute(type_counts_stmt)
            type_counts = {row.requirement_type.value: row.count for row in type_result}

            # Count by priority
            priority_counts_stmt = (
                select(
                    Requirement.priority,
                    func.count(Requirement.id).label('count')
                )
                .where(Requirement.project_id == project_id)
                .group_by(Requirement.priority)
            )
            priority_result = await self.db_session.execute(priority_counts_stmt)
            priority_counts = {row.priority.value: row.count for row in priority_result}

            # Total story points
            story_points_stmt = select(
                func.sum(Requirement.story_points)
            ).where(Requirement.project_id == project_id)
            story_points_result = await self.db_session.execute(story_points_stmt)
            total_story_points = story_points_result.scalar() or 0

            # Average business value
            business_value_stmt = select(
                func.avg(Requirement.business_value)
            ).where(Requirement.project_id == project_id)
            business_value_result = await self.db_session.execute(business_value_stmt)
            avg_business_value = business_value_result.scalar() or 0

            return {
                'project_id': project_id,
                'status_counts': status_counts,
                'type_counts': type_counts,
                'priority_counts': priority_counts,
                'total_story_points': int(total_story_points),
                'average_business_value': float(avg_business_value)
            }

        except Exception as e:
            logger.error("Error getting requirement stats", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to get requirement stats: {str(e)}")


class AcceptanceCriteriaRepository:
    """Repository for AcceptanceCriteria entity operations."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, criteria: AcceptanceCriteria) -> AcceptanceCriteria:
        """Create new acceptance criteria."""
        try:
            self.db_session.add(criteria)
            await self.db_session.flush()
            await self.db_session.refresh(criteria)
            return criteria
        except Exception as e:
            logger.error("Error creating acceptance criteria", error=str(e))
            raise DatabaseError(f"Failed to create acceptance criteria: {str(e)}")

    async def get_by_requirement(self, requirement_id: uuid.UUID) -> List[AcceptanceCriteria]:
        """Get acceptance criteria for a requirement."""
        try:
            stmt = (
                select(AcceptanceCriteria)
                .where(AcceptanceCriteria.requirement_id == requirement_id)
                .order_by(AcceptanceCriteria.order)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting acceptance criteria", requirement_id=str(requirement_id), error=str(e))
            raise DatabaseError(f"Failed to get acceptance criteria: {str(e)}")

    async def update(self, criteria: AcceptanceCriteria) -> AcceptanceCriteria:
        """Update acceptance criteria."""
        try:
            criteria.updated_at = datetime.utcnow()
            await self.db_session.flush()
            await self.db_session.refresh(criteria)
            return criteria
        except Exception as e:
            logger.error("Error updating acceptance criteria", criteria_id=str(criteria.id), error=str(e))
            raise DatabaseError(f"Failed to update acceptance criteria: {str(e)}")

    async def delete(self, criteria_id: uuid.UUID) -> bool:
        """Delete acceptance criteria."""
        try:
            stmt = select(AcceptanceCriteria).where(AcceptanceCriteria.id == criteria_id)
            result = await self.db_session.execute(stmt)
            criteria = result.scalar_one_or_none()

            if not criteria:
                return False

            await self.db_session.delete(criteria)
            await self.db_session.flush()
            return True
        except Exception as e:
            logger.error("Error deleting acceptance criteria", criteria_id=str(criteria_id), error=str(e))
            raise DatabaseError(f"Failed to delete acceptance criteria: {str(e)}")


class RequirementTemplateRepository:
    """Repository for RequirementTemplate entity operations."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, template: RequirementTemplate) -> RequirementTemplate:
        """Create a new requirement template."""
        try:
            self.db_session.add(template)
            await self.db_session.flush()
            await self.db_session.refresh(template)
            return template
        except Exception as e:
            logger.error("Error creating requirement template", error=str(e))
            raise DatabaseError(f"Failed to create requirement template: {str(e)}")

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> List[RequirementTemplate]:
        """Get templates by tenant."""
        try:
            stmt = (
                select(RequirementTemplate)
                .where(RequirementTemplate.tenant_id == tenant_id)
                .order_by(RequirementTemplate.name)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting templates by tenant", tenant_id=str(tenant_id), error=str(e))
            raise DatabaseError(f"Failed to get templates: {str(e)}")

    async def get_by_id(self, template_id: uuid.UUID) -> Optional[RequirementTemplate]:
        """Get template by ID."""
        try:
            stmt = select(RequirementTemplate).where(RequirementTemplate.id == template_id)
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting template by ID", template_id=str(template_id), error=str(e))
            raise DatabaseError(f"Failed to get template: {str(e)}")
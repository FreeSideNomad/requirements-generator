"""
Repository layer for Project domain.
Handles data access and persistence operations for projects.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import structlog

from ..shared.exceptions import NotFoundError, DatabaseError
from .models import Project, ProjectMember
from ..requirements.models import Requirement


logger = structlog.get_logger(__name__)


class ProjectRepository:
    """Repository for Project entity operations."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, project: Project) -> Project:
        """Create a new project."""
        try:
            self.db_session.add(project)
            await self.db_session.flush()
            await self.db_session.refresh(project)
            return project
        except Exception as e:
            logger.error("Error creating project", error=str(e))
            raise DatabaseError(f"Failed to create project: {str(e)}")

    async def get_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID."""
        try:
            stmt = select(Project).where(Project.id == project_id)
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting project by ID", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to get project: {str(e)}")

    async def get_by_id_with_members(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID with members loaded."""
        try:
            stmt = (
                select(Project)
                .options(selectinload(Project.members))
                .where(Project.id == project_id)
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting project with members", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to get project with members: {str(e)}")

    async def get_by_tenant(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get projects by tenant with pagination."""
        try:
            stmt = (
                select(Project)
                .where(Project.tenant_id == tenant_id)
                .order_by(desc(Project.created_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting projects by tenant", tenant_id=str(tenant_id), error=str(e))
            raise DatabaseError(f"Failed to get projects: {str(e)}")

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get projects where user is a member."""
        try:
            stmt = (
                select(Project)
                .join(ProjectMember, Project.id == ProjectMember.project_id)
                .where(
                    and_(
                        ProjectMember.user_id == user_id,
                        Project.tenant_id == tenant_id
                    )
                )
                .order_by(desc(Project.updated_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting projects by user", user_id=str(user_id), error=str(e))
            raise DatabaseError(f"Failed to get user projects: {str(e)}")

    async def update(self, project: Project) -> Project:
        """Update a project."""
        try:
            project.updated_at = datetime.utcnow()
            await self.db_session.flush()
            await self.db_session.refresh(project)
            return project
        except Exception as e:
            logger.error("Error updating project", project_id=str(project.id), error=str(e))
            raise DatabaseError(f"Failed to update project: {str(e)}")

    async def delete(self, project_id: uuid.UUID) -> bool:
        """Delete a project."""
        try:
            stmt = select(Project).where(Project.id == project_id)
            result = await self.db_session.execute(stmt)
            project = result.scalar_one_or_none()

            if not project:
                return False

            await self.db_session.delete(project)
            await self.db_session.flush()
            return True
        except Exception as e:
            logger.error("Error deleting project", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to delete project: {str(e)}")

    async def count_by_tenant(self, tenant_id: uuid.UUID) -> int:
        """Count projects by tenant."""
        try:
            stmt = select(func.count(Project.id)).where(Project.tenant_id == tenant_id)
            result = await self.db_session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error("Error counting projects", tenant_id=str(tenant_id), error=str(e))
            raise DatabaseError(f"Failed to count projects: {str(e)}")

    async def search(
        self,
        tenant_id: uuid.UUID,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Project]:
        """Search projects by name or description."""
        try:
            search_term = f"%{query}%"
            stmt = (
                select(Project)
                .where(
                    and_(
                        Project.tenant_id == tenant_id,
                        or_(
                            Project.name.ilike(search_term),
                            Project.description.ilike(search_term)
                        )
                    )
                )
                .order_by(desc(Project.updated_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error searching projects", query=query, error=str(e))
            raise DatabaseError(f"Failed to search projects: {str(e)}")

    async def get_project_stats(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """Get project statistics."""
        try:
            # Count requirements by status
            requirements_count_stmt = (
                select(
                    Requirement.status,
                    func.count(Requirement.id).label('count')
                )
                .where(Requirement.project_id == project_id)
                .group_by(Requirement.status)
            )
            requirements_result = await self.db_session.execute(requirements_count_stmt)
            requirements_by_status = {row.status: row.count for row in requirements_result}

            # Total requirements count
            total_requirements_stmt = select(func.count(Requirement.id)).where(
                Requirement.project_id == project_id
            )
            total_requirements_result = await self.db_session.execute(total_requirements_stmt)
            total_requirements = total_requirements_result.scalar() or 0

            # Members count
            members_count_stmt = select(func.count(ProjectMember.id)).where(
                ProjectMember.project_id == project_id
            )
            members_result = await self.db_session.execute(members_count_stmt)
            members_count = members_result.scalar() or 0

            # Get project details
            project = await self.get_by_id(project_id)
            if not project:
                raise NotFoundError("Project", str(project_id))

            return {
                'project_id': project_id,
                'total_requirements': total_requirements,
                'requirements_by_status': requirements_by_status,
                'members_count': members_count,
                'created_at': project.created_at,
                'last_updated': project.updated_at
            }

        except Exception as e:
            logger.error("Error getting project stats", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to get project stats: {str(e)}")


class ProjectMemberRepository:
    """Repository for ProjectMember entity operations."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_member(self, project_member: ProjectMember) -> ProjectMember:
        """Add a member to a project."""
        try:
            self.db_session.add(project_member)
            await self.db_session.flush()
            await self.db_session.refresh(project_member)
            return project_member
        except Exception as e:
            logger.error("Error adding project member", error=str(e))
            raise DatabaseError(f"Failed to add project member: {str(e)}")

    async def remove_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Remove a member from a project."""
        try:
            stmt = select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                )
            )
            result = await self.db_session.execute(stmt)
            member = result.scalar_one_or_none()

            if not member:
                return False

            await self.db_session.delete(member)
            await self.db_session.flush()
            return True
        except Exception as e:
            logger.error(
                "Error removing project member",
                project_id=str(project_id),
                user_id=str(user_id),
                error=str(e)
            )
            raise DatabaseError(f"Failed to remove project member: {str(e)}")

    async def get_project_members(self, project_id: uuid.UUID) -> List[ProjectMember]:
        """Get all members of a project."""
        try:
            stmt = (
                select(ProjectMember)
                .where(ProjectMember.project_id == project_id)
                .order_by(ProjectMember.created_at)
            )
            result = await self.db_session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting project members", project_id=str(project_id), error=str(e))
            raise DatabaseError(f"Failed to get project members: {str(e)}")

    async def is_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if user is a member of the project."""
        try:
            stmt = select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                )
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(
                "Error checking project membership",
                project_id=str(project_id),
                user_id=str(user_id),
                error=str(e)
            )
            raise DatabaseError(f"Failed to check project membership: {str(e)}")

    async def update_member_role(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        new_role: str
    ) -> Optional[ProjectMember]:
        """Update a member's role in the project."""
        try:
            stmt = select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                )
            )
            result = await self.db_session.execute(stmt)
            member = result.scalar_one_or_none()

            if not member:
                return None

            member.role = new_role
            member.updated_at = datetime.utcnow()
            await self.db_session.flush()
            await self.db_session.refresh(member)
            return member
        except Exception as e:
            logger.error(
                "Error updating member role",
                project_id=str(project_id),
                user_id=str(user_id),
                error=str(e)
            )
            raise DatabaseError(f"Failed to update member role: {str(e)}")
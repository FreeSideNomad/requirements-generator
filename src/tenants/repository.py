"""
Tenant repository layer for database operations.
Implements data access patterns with SQLAlchemy async operations.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..shared.database import get_db_session
from ..shared.exceptions import NotFoundError, ConflictError, DatabaseError
from ..shared.tenant_middleware import RowLevelSecurityMixin
from .models import Tenant, TenantInvitation, TenantFeature, TenantStatus, Industry, SubscriptionTier
from .schemas import TenantCreate, TenantUpdate


class TenantRepository:
    """Repository for tenant data access operations."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        async for session in get_db_session():
            return session

    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """Create a new tenant."""
        async with await self._get_session() as session:
            try:
                # Check for subdomain conflicts
                existing = await self.get_by_subdomain(tenant_data.subdomain)
                if existing:
                    raise ConflictError(f"Subdomain '{tenant_data.subdomain}' already exists")

                # Check for custom domain conflicts
                if tenant_data.custom_domain:
                    existing_domain = await self.get_by_custom_domain(tenant_data.custom_domain)
                    if existing_domain:
                        raise ConflictError(f"Domain '{tenant_data.custom_domain}' already exists")

                # Create tenant with trial period
                trial_ends_at = datetime.utcnow() + timedelta(days=30)  # 30-day trial

                tenant = Tenant(
                    name=tenant_data.name,
                    subdomain=tenant_data.subdomain.lower(),
                    custom_domain=tenant_data.custom_domain,
                    industry=tenant_data.industry,
                    subscription_tier=tenant_data.subscription_tier,
                    max_users=tenant_data.max_users,
                    max_projects=tenant_data.max_projects,
                    billing_email=tenant_data.billing_email,
                    technical_contact=tenant_data.technical_contact,
                    template_config=tenant_data.template_config or {},
                    features=tenant_data.features or {},
                    settings=tenant_data.settings or {},
                    status=TenantStatus.TRIAL,
                    trial_ends_at=trial_ends_at,
                    is_active=True
                )

                session.add(tenant)
                await session.commit()
                await session.refresh(tenant)

                return tenant

            except Exception as e:
                await session.rollback()
                if isinstance(e, (ConflictError, NotFoundError)):
                    raise
                raise DatabaseError(f"Failed to create tenant: {str(e)}")

    async def get_tenant_by_id(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        """Get tenant by ID."""
        async with await self._get_session() as session:
            try:
                stmt = select(Tenant).where(Tenant.id == tenant_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get tenant: {str(e)}")

    async def get_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """Get tenant by subdomain."""
        async with await self._get_session() as session:
            try:
                stmt = select(Tenant).where(Tenant.subdomain == subdomain.lower())
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get tenant by subdomain: {str(e)}")

    async def get_by_custom_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by custom domain."""
        async with await self._get_session() as session:
            try:
                stmt = select(Tenant).where(Tenant.custom_domain == domain)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get tenant by domain: {str(e)}")

    async def update_tenant(self, tenant_id: uuid.UUID, update_data: TenantUpdate) -> Optional[Tenant]:
        """Update an existing tenant."""
        async with await self._get_session() as session:
            try:
                # Get existing tenant
                tenant = await self.get_tenant_by_id(tenant_id)
                if not tenant:
                    raise NotFoundError("Tenant", str(tenant_id))

                # Prepare update data, excluding None values
                update_dict = update_data.model_dump(exclude_none=True)

                if update_dict:
                    # Check for subdomain conflicts if subdomain is being updated
                    if "subdomain" in update_dict:
                        existing = await self.get_by_subdomain(update_dict["subdomain"])
                        if existing and existing.id != tenant_id:
                            raise ConflictError(f"Subdomain '{update_dict['subdomain']}' already exists")

                    # Check for custom domain conflicts if domain is being updated
                    if "custom_domain" in update_dict and update_dict["custom_domain"]:
                        existing_domain = await self.get_by_custom_domain(update_dict["custom_domain"])
                        if existing_domain and existing_domain.id != tenant_id:
                            raise ConflictError(f"Domain '{update_dict['custom_domain']}' already exists")

                    # Update timestamp
                    update_dict["updated_at"] = datetime.utcnow()

                    # Apply updates
                    stmt = (
                        update(Tenant)
                        .where(Tenant.id == tenant_id)
                        .values(**update_dict)
                        .execution_options(synchronize_session=False)
                    )
                    await session.execute(stmt)
                    await session.commit()

                # Return updated tenant
                return await self.get_tenant_by_id(tenant_id)

            except Exception as e:
                await session.rollback()
                if isinstance(e, (ConflictError, NotFoundError)):
                    raise
                raise DatabaseError(f"Failed to update tenant: {str(e)}")

    async def delete_tenant(self, tenant_id: uuid.UUID) -> bool:
        """Delete a tenant (soft delete by deactivating)."""
        async with await self._get_session() as session:
            try:
                tenant = await self.get_tenant_by_id(tenant_id)
                if not tenant:
                    raise NotFoundError("Tenant", str(tenant_id))

                # Soft delete by setting status and is_active
                stmt = (
                    update(Tenant)
                    .where(Tenant.id == tenant_id)
                    .values(
                        status=TenantStatus.CANCELLED,
                        is_active=False,
                        updated_at=datetime.utcnow()
                    )
                    .execution_options(synchronize_session=False)
                )
                await session.execute(stmt)
                await session.commit()

                return True

            except Exception as e:
                await session.rollback()
                if isinstance(e, NotFoundError):
                    raise
                raise DatabaseError(f"Failed to delete tenant: {str(e)}")

    async def list_tenants(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[TenantStatus] = None,
        industry: Optional[Industry] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> Tuple[List[Tenant], int]:
        """List tenants with filtering and pagination."""
        async with await self._get_session() as session:
            try:
                # Base query
                query = select(Tenant)

                # Apply filters
                conditions = []

                if active_only:
                    conditions.append(Tenant.is_active == True)

                if status:
                    conditions.append(Tenant.status == status)

                if industry:
                    conditions.append(Tenant.industry == industry)

                if subscription_tier:
                    conditions.append(Tenant.subscription_tier == subscription_tier)

                if search:
                    search_pattern = f"%{search.lower()}%"
                    conditions.append(
                        or_(
                            func.lower(Tenant.name).like(search_pattern),
                            func.lower(Tenant.subdomain).like(search_pattern)
                        )
                    )

                if conditions:
                    query = query.where(and_(*conditions))

                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                total_result = await session.execute(count_query)
                total = total_result.scalar()

                # Apply ordering and pagination
                query = query.order_by(Tenant.created_at.desc()).offset(skip).limit(limit)

                # Execute query
                result = await session.execute(query)
                tenants = result.scalars().all()

                return list(tenants), total

            except Exception as e:
                raise DatabaseError(f"Failed to list tenants: {str(e)}")

    async def get_tenant_stats(self, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Get tenant usage statistics."""
        async with await self._get_session() as session:
            try:
                tenant = await self.get_tenant_by_id(tenant_id)
                if not tenant:
                    raise NotFoundError("Tenant", str(tenant_id))

                # Get actual tenant statistics
                stats = await self._calculate_tenant_stats(session, tenant_id)

                return stats

            except Exception as e:
                if isinstance(e, NotFoundError):
                    raise
                raise DatabaseError(f"Failed to get tenant stats: {str(e)}")

    async def activate_tenant(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        """Activate a tenant."""
        return await self.update_tenant(
            tenant_id,
            TenantUpdate(status=TenantStatus.ACTIVE, is_active=True)
        )

    async def suspend_tenant(self, tenant_id: uuid.UUID, reason: Optional[str] = None) -> Optional[Tenant]:
        """Suspend a tenant."""
        return await self.update_tenant(
            tenant_id,
            TenantUpdate(
                status=TenantStatus.SUSPENDED,
                is_active=False,
                suspended_at=datetime.utcnow()
            )
        )

    async def get_trial_expiring_tenants(self, days_ahead: int = 7) -> List[Tenant]:
        """Get tenants whose trial is expiring within specified days."""
        async with await self._get_session() as session:
            try:
                cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)

                stmt = select(Tenant).where(
                    and_(
                        Tenant.status == TenantStatus.TRIAL,
                        Tenant.trial_ends_at <= cutoff_date,
                        Tenant.is_active == True
                    )
                ).order_by(Tenant.trial_ends_at)

                result = await session.execute(stmt)
                return list(result.scalars().all())

            except Exception as e:
                raise DatabaseError(f"Failed to get trial expiring tenants: {str(e)}")

    async def get_tenants_by_industry(self, industry: Industry) -> List[Tenant]:
        """Get all active tenants in a specific industry."""
        async with await self._get_session() as session:
            try:
                stmt = select(Tenant).where(
                    and_(
                        Tenant.industry == industry,
                        Tenant.is_active == True
                    )
                ).order_by(Tenant.name)

                result = await session.execute(stmt)
                return list(result.scalars().all())

            except Exception as e:
                raise DatabaseError(f"Failed to get tenants by industry: {str(e)}")

    async def _calculate_tenant_stats(self, session: AsyncSession, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Calculate actual tenant statistics."""
        from ..auth.models import User  # Import here to avoid circular imports
        from ..projects.models import Project
        from ..requirements.models import Requirement

        try:
            # Count active users
            users_stmt = select(func.count(User.id)).where(
                and_(
                    User.tenant_id == tenant_id,
                    User.is_active == True
                )
            )
            users_result = await session.execute(users_stmt)
            current_users = users_result.scalar() or 0

            # Count active projects
            projects_stmt = select(func.count(Project.id)).where(
                Project.tenant_id == tenant_id
            )
            projects_result = await session.execute(projects_stmt)
            current_projects = projects_result.scalar() or 0

            # Count total requirements (as a measure of usage)
            requirements_stmt = select(func.count(Requirement.id)).where(
                Requirement.project_id.in_(
                    select(Project.id).where(Project.tenant_id == tenant_id)
                )
            )
            requirements_result = await session.execute(requirements_stmt)
            total_requirements = requirements_result.scalar() or 0

            # Get last activity (most recent project update or user login)
            last_project_activity_stmt = select(func.max(Project.updated_at)).where(
                Project.tenant_id == tenant_id
            )
            last_project_result = await session.execute(last_project_activity_stmt)
            last_project_activity = last_project_result.scalar()

            last_user_activity_stmt = select(func.max(User.last_login)).where(
                User.tenant_id == tenant_id
            )
            last_user_result = await session.execute(last_user_activity_stmt)
            last_user_activity = last_user_result.scalar()

            # Determine the most recent activity
            last_activity = None
            if last_project_activity and last_user_activity:
                last_activity = max(last_project_activity, last_user_activity)
            elif last_project_activity:
                last_activity = last_project_activity
            elif last_user_activity:
                last_activity = last_user_activity

            # Estimate storage usage (rough calculation based on content)
            # This is a simplified calculation - in production you'd want more sophisticated tracking
            storage_estimation = (
                (current_projects * 0.1) +  # ~0.1MB per project
                (total_requirements * 0.01) +  # ~0.01MB per requirement
                (current_users * 0.05)  # ~0.05MB per user
            )

            return {
                "tenant_id": tenant_id,
                "current_users": current_users,
                "current_projects": current_projects,
                "total_requirements": total_requirements,
                "storage_used_mb": round(storage_estimation, 2),
                "api_calls_today": 0,  # This would require API call tracking
                "last_activity": last_activity.isoformat() if last_activity else None
            }

        except Exception as e:
            logger.error("Error calculating tenant stats", tenant_id=str(tenant_id), error=str(e))
            # Return basic stats if detailed calculation fails
            return {
                "tenant_id": tenant_id,
                "current_users": 0,
                "current_projects": 0,
                "total_requirements": 0,
                "storage_used_mb": 0.0,
                "api_calls_today": 0,
                "last_activity": None
            }
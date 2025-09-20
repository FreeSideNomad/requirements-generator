"""
User and authentication repository for database operations.
Supports full user management within the application for development purposes.
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
from .models import User, UserSession, UserInvitation, UserRole, UserStatus, AuthProvider
from .schemas import UserProfileUpdate


class UserRepository(RowLevelSecurityMixin):
    """Repository for user and authentication data access."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        async for session in get_db_session():
            return session

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        async with await self._get_session() as session:
            try:
                # Check for email conflicts
                existing = await self.get_user_by_email(user_data["email"])
                if existing:
                    raise ConflictError(f"User with email '{user_data['email']}' already exists")

                # Check for username conflicts within tenant
                if user_data.get("username"):
                    existing_username = await self.get_user_by_username(
                        user_data["username"],
                        user_data["tenant_id"]
                    )
                    if existing_username:
                        raise ConflictError(f"Username '{user_data['username']}' already exists in this tenant")

                user = User(**user_data)
                session.add(user)
                await session.commit()
                await session.refresh(user)

                return user

            except Exception as e:
                await session.rollback()
                if isinstance(e, ConflictError):
                    raise
                raise DatabaseError(f"Failed to create user: {str(e)}")

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        async with await self._get_session() as session:
            try:
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get user: {str(e)}")

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        async with await self._get_session() as session:
            try:
                stmt = select(User).where(func.lower(User.email) == email.lower())
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get user by email: {str(e)}")

    async def get_user_by_username(self, username: str, tenant_id: uuid.UUID) -> Optional[User]:
        """Get user by username within a tenant."""
        async with await self._get_session() as session:
            try:
                stmt = select(User).where(
                    and_(
                        func.lower(User.username) == username.lower(),
                        User.tenant_id == tenant_id
                    )
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get user by username: {str(e)}")

    async def update_user_profile(self, user_id: uuid.UUID, update_data: UserProfileUpdate) -> Optional[User]:
        """Update user profile information."""
        async with await self._get_session() as session:
            try:
                user = await self.get_user_by_id(user_id)
                if not user:
                    raise NotFoundError("User", str(user_id))

                # Prepare update data, excluding None values
                update_dict = update_data.model_dump(exclude_none=True)

                if update_dict:
                    # Check for username conflicts if username is being updated
                    if "username" in update_dict:
                        existing = await self.get_user_by_username(update_dict["username"], user.tenant_id)
                        if existing and existing.id != user_id:
                            raise ConflictError(f"Username '{update_dict['username']}' already exists")

                    # Handle preferences separately for proper JSON merge
                    if "preferences" in update_dict:
                        current_prefs = user.preferences or {}
                        new_prefs = update_dict["preferences"] or {}
                        update_dict["preferences"] = {**current_prefs, **new_prefs}

                    # Update timestamp
                    update_dict["updated_at"] = datetime.utcnow()

                    # Apply updates
                    stmt = (
                        update(User)
                        .where(User.id == user_id)
                        .values(**update_dict)
                        .execution_options(synchronize_session=False)
                    )
                    await session.execute(stmt)
                    await session.commit()

                # Return updated user
                return await self.get_user_by_id(user_id)

            except Exception as e:
                await session.rollback()
                if isinstance(e, (ConflictError, NotFoundError)):
                    raise
                raise DatabaseError(f"Failed to update user: {str(e)}")

    async def update_password(self, user_id: uuid.UUID, password_hash: str) -> bool:
        """Update user password."""
        async with await self._get_session() as session:
            try:
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        password_hash=password_hash,
                        password_changed_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    .execution_options(synchronize_session=False)
                )
                result = await session.execute(stmt)
                await session.commit()

                return result.rowcount > 0

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update password: {str(e)}")

    async def update_last_login(self, user_id: uuid.UUID) -> bool:
        """Update user's last login timestamp."""
        async with await self._get_session() as session:
            try:
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(last_login_at=datetime.utcnow())
                    .execution_options(synchronize_session=False)
                )
                result = await session.execute(stmt)
                await session.commit()

                return result.rowcount > 0

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update last login: {str(e)}")

    async def update_user_status(self, user_id: uuid.UUID, status: UserStatus, is_active: bool = None) -> Optional[User]:
        """Update user status and active flag."""
        async with await self._get_session() as session:
            try:
                update_data = {"status": status, "updated_at": datetime.utcnow()}
                if is_active is not None:
                    update_data["is_active"] = is_active

                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data)
                    .execution_options(synchronize_session=False)
                )
                await session.execute(stmt)
                await session.commit()

                return await self.get_user_by_id(user_id)

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update user status: {str(e)}")

    async def list_users(
        self,
        tenant_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> Tuple[List[User], int]:
        """List users with filtering and pagination."""
        async with await self._get_session() as session:
            try:
                # Base query
                query = select(User)

                # Apply filters
                conditions = []

                if tenant_id:
                    conditions.append(User.tenant_id == tenant_id)

                if active_only:
                    conditions.append(User.is_active == True)

                if status:
                    conditions.append(User.status == status)

                if role:
                    conditions.append(User.role == role)

                if search:
                    search_pattern = f"%{search.lower()}%"
                    conditions.append(
                        or_(
                            func.lower(User.first_name).like(search_pattern),
                            func.lower(User.last_name).like(search_pattern),
                            func.lower(User.email).like(search_pattern),
                            func.lower(User.username).like(search_pattern)
                        )
                    )

                if conditions:
                    query = query.where(and_(*conditions))

                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                total_result = await session.execute(count_query)
                total = total_result.scalar()

                # Apply ordering and pagination
                query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)

                # Execute query
                result = await session.execute(query)
                users = result.scalars().all()

                return list(users), total

            except Exception as e:
                raise DatabaseError(f"Failed to list users: {str(e)}")

    async def delete_user(self, user_id: uuid.UUID, soft_delete: bool = True) -> bool:
        """Delete user (soft delete by default)."""
        async with await self._get_session() as session:
            try:
                if soft_delete:
                    # Soft delete by deactivating
                    stmt = (
                        update(User)
                        .where(User.id == user_id)
                        .values(
                            is_active=False,
                            status=UserStatus.INACTIVE,
                            updated_at=datetime.utcnow()
                        )
                        .execution_options(synchronize_session=False)
                    )
                else:
                    # Hard delete
                    stmt = delete(User).where(User.id == user_id)

                result = await session.execute(stmt)
                await session.commit()

                return result.rowcount > 0

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to delete user: {str(e)}")

    # Session management methods

    async def create_session(self, session_data: Dict[str, Any]) -> UserSession:
        """Create a new user session."""
        async with await self._get_session() as session:
            try:
                user_session = UserSession(**session_data)
                session.add(user_session)
                await session.commit()
                await session.refresh(user_session)

                return user_session

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to create session: {str(e)}")

    async def get_session_by_token(self, session_token: str) -> Optional[UserSession]:
        """Get session by token."""
        async with await self._get_session() as session:
            try:
                stmt = select(UserSession).where(UserSession.session_token == session_token)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get session: {str(e)}")

    async def invalidate_session(self, user_id: uuid.UUID, session_token: str) -> bool:
        """Invalidate a specific session."""
        async with await self._get_session() as session:
            try:
                stmt = (
                    update(UserSession)
                    .where(
                        and_(
                            UserSession.user_id == user_id,
                            UserSession.session_token == session_token
                        )
                    )
                    .values(
                        is_active=False,
                        terminated_at=datetime.utcnow()
                    )
                    .execution_options(synchronize_session=False)
                )
                result = await session.execute(stmt)
                await session.commit()

                return result.rowcount > 0

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to invalidate session: {str(e)}")

    async def invalidate_all_sessions(self, user_id: uuid.UUID) -> bool:
        """Invalidate all sessions for a user."""
        async with await self._get_session() as session:
            try:
                stmt = (
                    update(UserSession)
                    .where(UserSession.user_id == user_id)
                    .values(
                        is_active=False,
                        terminated_at=datetime.utcnow()
                    )
                    .execution_options(synchronize_session=False)
                )
                result = await session.execute(stmt)
                await session.commit()

                return result.rowcount > 0

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to invalidate sessions: {str(e)}")

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        async with await self._get_session() as session:
            try:
                now = datetime.utcnow()
                stmt = (
                    update(UserSession)
                    .where(
                        and_(
                            UserSession.expires_at < now,
                            UserSession.is_active == True
                        )
                    )
                    .values(
                        is_active=False,
                        terminated_at=now
                    )
                    .execution_options(synchronize_session=False)
                )
                result = await session.execute(stmt)
                await session.commit()

                return result.rowcount

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to cleanup sessions: {str(e)}")

    # Invitation management methods

    async def create_invitation(
        self,
        email: str,
        tenant_id: uuid.UUID,
        role: UserRole,
        invited_by_id: uuid.UUID,
        token: str,
        message: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        expires_days: int = 7
    ) -> UserInvitation:
        """Create a user invitation."""
        async with await self._get_session() as session:
            try:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)

                invitation = UserInvitation(
                    email=email,
                    token=token,
                    tenant_id=tenant_id,
                    role=role,
                    invited_by_id=invited_by_id,
                    message=message,
                    permissions=permissions or {},
                    expires_at=expires_at
                )

                session.add(invitation)
                await session.commit()
                await session.refresh(invitation)

                return invitation

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to create invitation: {str(e)}")

    async def get_invitation_by_token(self, token: str) -> Optional[UserInvitation]:
        """Get invitation by token."""
        async with await self._get_session() as session:
            try:
                stmt = select(UserInvitation).where(UserInvitation.token == token)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise DatabaseError(f"Failed to get invitation: {str(e)}")

    async def mark_invitation_used(self, invitation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Mark invitation as used."""
        async with await self._get_session() as session:
            try:
                stmt = (
                    update(UserInvitation)
                    .where(UserInvitation.id == invitation_id)
                    .values(
                        is_used=True,
                        used_at=datetime.utcnow(),
                        user_id=user_id
                    )
                    .execution_options(synchronize_session=False)
                )
                result = await session.execute(stmt)
                await session.commit()

                return result.rowcount > 0

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to mark invitation as used: {str(e)}")

    async def get_users_by_tenant(self, tenant_id: uuid.UUID) -> List[User]:
        """Get all users for a specific tenant."""
        async with await self._get_session() as session:
            try:
                stmt = select(User).where(
                    and_(
                        User.tenant_id == tenant_id,
                        User.is_active == True
                    )
                ).order_by(User.created_at)

                result = await session.execute(stmt)
                return list(result.scalars().all())

            except Exception as e:
                raise DatabaseError(f"Failed to get users by tenant: {str(e)}")

    async def update_user_role(self, user_id: uuid.UUID, role: UserRole, permissions: Optional[Dict[str, Any]] = None) -> Optional[User]:
        """Update user role and permissions."""
        async with await self._get_session() as session:
            try:
                update_data = {
                    "role": role,
                    "updated_at": datetime.utcnow()
                }

                if permissions is not None:
                    update_data["permissions"] = permissions

                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data)
                    .execution_options(synchronize_session=False)
                )
                await session.execute(stmt)
                await session.commit()

                return await self.get_user_by_id(user_id)

            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update user role: {str(e)}")
"""
Shared FastAPI dependencies for request processing.
Provides common dependencies like database sessions and tenant context.
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db_session as _get_db_session
from ..tenants.schemas import TenantResponse


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    async for session in _get_db_session():
        yield session


async def get_current_tenant(request: Request) -> TenantResponse:
    """
    Get current tenant from request context.
    This is a placeholder implementation that would be populated by tenant middleware.
    """
    # In a real implementation, this would get the tenant from request state
    # set by the tenant middleware based on subdomain or other tenant identification

    # For now, return a mock tenant for development
    now = datetime.utcnow()
    return TenantResponse(
        id=uuid.UUID("12345678-1234-5678-9abc-123456789012"),
        name="Default Tenant",
        subdomain="default",
        plan="premium",
        is_active=True,
        settings={},
        created_at=now,
        updated_at=now
    )


async def get_tenant_context(request: Request) -> dict:
    """Get tenant context from request state."""
    return getattr(request.state, 'tenant_context', {})


async def require_admin_role(request: Request) -> None:
    """Dependency that requires admin role."""
    tenant_context = await get_tenant_context(request)
    user_role = tenant_context.get('user_role')

    if user_role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )


async def require_authenticated(request: Request) -> None:
    """Dependency that requires authentication."""
    tenant_context = await get_tenant_context(request)
    is_authenticated = tenant_context.get('is_authenticated', False)

    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
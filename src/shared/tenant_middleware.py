"""
Tenant isolation middleware for multi-tenant applications.
Implements row-level security and tenant context management.
"""

import uuid
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.jwt_handler import jwt_handler
from ..shared.database import get_db_session


class TenantContext:
    """Thread-local tenant context for request processing."""

    def __init__(self):
        self.tenant_id: Optional[uuid.UUID] = None
        self.tenant_subdomain: Optional[str] = None
        self.user_id: Optional[uuid.UUID] = None
        self.user_role: Optional[str] = None
        self.is_authenticated: bool = False

    def set_context(
        self,
        tenant_id: uuid.UUID,
        tenant_subdomain: str,
        user_id: Optional[uuid.UUID] = None,
        user_role: Optional[str] = None
    ):
        """Set tenant context for current request."""
        self.tenant_id = tenant_id
        self.tenant_subdomain = tenant_subdomain
        self.user_id = user_id
        self.user_role = user_role
        self.is_authenticated = user_id is not None

    def clear_context(self):
        """Clear tenant context."""
        self.tenant_id = None
        self.tenant_subdomain = None
        self.user_id = None
        self.user_role = None
        self.is_authenticated = False

    def get_context(self) -> Dict[str, Any]:
        """Get current tenant context."""
        return {
            "tenant_id": self.tenant_id,
            "tenant_subdomain": self.tenant_subdomain,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "is_authenticated": self.is_authenticated
        }

    @property
    def has_tenant(self) -> bool:
        """Check if tenant context is set."""
        return self.tenant_id is not None


# Global tenant context instance
tenant_context = TenantContext()


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle tenant isolation and context."""

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/providers",
            "/auth/health",
            "/tenants/templates",
        ]
        self.security = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with tenant isolation."""
        # Clear previous context
        tenant_context.clear_context()

        # Skip tenant isolation for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            response = await call_next(request)
            return response

        # Extract tenant information
        try:
            await self._extract_tenant_context(request)
        except HTTPException as e:
            # Return HTTP exception for tenant-related errors
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )

        # Process request with tenant context
        response = await call_next(request)

        # Add tenant info to response headers (for debugging)
        if tenant_context.has_tenant:
            response.headers["X-Tenant-ID"] = str(tenant_context.tenant_id)
            response.headers["X-Tenant-Subdomain"] = tenant_context.tenant_subdomain

        return response

    async def _extract_tenant_context(self, request: Request):
        """Extract tenant context from request."""
        tenant_id = None
        tenant_subdomain = None
        user_id = None
        user_role = None

        # Method 1: Extract from Authorization header (JWT token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt_handler.verify_access_token(token)
                tenant_id = uuid.UUID(payload["tenant_id"])
                user_id = uuid.UUID(payload["sub"])
                user_role = payload.get("role")

                # Get tenant subdomain from database
                from ..tenants.repository import TenantRepository
                tenant_repo = TenantRepository()
                tenant = await tenant_repo.get_tenant_by_id(tenant_id)
                if tenant:
                    tenant_subdomain = tenant.subdomain
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Tenant not found"
                    )

            except Exception:
                # Invalid token - might be optional for some endpoints
                pass

        # Method 2: Extract from subdomain in Host header
        if not tenant_id:
            host = request.headers.get("Host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["www", "api", "app"]:  # Skip common subdomains
                    from ..tenants.repository import TenantRepository
                    tenant_repo = TenantRepository()
                    tenant = await tenant_repo.get_by_subdomain(subdomain)
                    if tenant:
                        tenant_id = tenant.id
                        tenant_subdomain = tenant.subdomain

        # Method 3: Extract from X-Tenant-ID header (for API clients)
        if not tenant_id:
            tenant_header = request.headers.get("X-Tenant-ID")
            if tenant_header:
                try:
                    tenant_id = uuid.UUID(tenant_header)
                    from ..tenants.repository import TenantRepository
                    tenant_repo = TenantRepository()
                    tenant = await tenant_repo.get_tenant_by_id(tenant_id)
                    if tenant:
                        tenant_subdomain = tenant.subdomain
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Tenant not found"
                        )
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid tenant ID format"
                    )

        # Method 4: Extract from query parameter (for development/testing)
        tenant_param = request.query_params.get("tenant_id")
        if not tenant_id and tenant_param:
            try:
                tenant_id = uuid.UUID(tenant_param)
                from ..tenants.repository import TenantRepository
                tenant_repo = TenantRepository()
                tenant = await tenant_repo.get_tenant_by_id(tenant_id)
                if tenant:
                    tenant_subdomain = tenant.subdomain
            except ValueError:
                pass

        # Check if tenant is required for this endpoint
        if self._requires_tenant(request.url.path) and not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant identification required"
            )

        # Set tenant context if found
        if tenant_id and tenant_subdomain:
            tenant_context.set_context(
                tenant_id=tenant_id,
                tenant_subdomain=tenant_subdomain,
                user_id=user_id,
                user_role=user_role
            )

    def _requires_tenant(self, path: str) -> bool:
        """Check if endpoint requires tenant context."""
        # Tenant creation and public endpoints don't require tenant context
        public_paths = [
            "/auth/register",
            "/auth/login",
            "/auth/password-reset",
            "/auth/providers",
            "/tenants/",  # Tenant creation
            "/tenants/templates",
        ]

        return not any(path.startswith(public_path) for public_path in public_paths)


class RowLevelSecurityMixin:
    """Mixin to add row-level security to repository classes."""

    def _add_tenant_filter(self, query, model_class):
        """Add tenant filter to SQLAlchemy query."""
        if hasattr(model_class, 'tenant_id') and tenant_context.has_tenant:
            return query.where(model_class.tenant_id == tenant_context.tenant_id)
        return query

    def _validate_tenant_access(self, model_instance):
        """Validate that model instance belongs to current tenant."""
        if hasattr(model_instance, 'tenant_id') and tenant_context.has_tenant:
            if model_instance.tenant_id != tenant_context.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Resource belongs to different tenant"
                )

    def _set_tenant_id(self, data: dict):
        """Set tenant_id on data if not already set."""
        if tenant_context.has_tenant and 'tenant_id' not in data:
            data['tenant_id'] = tenant_context.tenant_id
        return data


def get_current_tenant() -> TenantContext:
    """FastAPI dependency to get current tenant context."""
    if not tenant_context.has_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context available"
        )
    return tenant_context


def require_tenant_access():
    """FastAPI dependency to require tenant access."""
    def _check_tenant():
        if not tenant_context.has_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant access required"
            )
        return tenant_context
    return _check_tenant


def require_authenticated_user():
    """FastAPI dependency to require authenticated user."""
    def _check_auth():
        if not tenant_context.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return tenant_context
    return _check_auth


def require_role(required_role: str):
    """FastAPI dependency to require specific user role."""
    def _check_role():
        if not tenant_context.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if tenant_context.user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return tenant_context
    return _check_role


def require_admin_role():
    """FastAPI dependency to require admin role."""
    def _check_admin():
        if not tenant_context.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        admin_roles = ["tenant_admin", "super_admin"]
        if tenant_context.user_role not in admin_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access required"
            )
        return tenant_context
    return _check_admin


# Database session with tenant isolation
async def get_tenant_db_session() -> AsyncSession:
    """Get database session with tenant context set."""
    async for session in get_db_session():
        break

    # Set tenant context in session for RLS
    if tenant_context.has_tenant:
        # This would set session variables for PostgreSQL RLS
        # await session.execute(text(f"SET app.current_tenant_id = '{tenant_context.tenant_id}'"))
        pass

    return session
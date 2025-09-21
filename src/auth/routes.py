"""
Authentication API routes.
Handles user authentication, session management, and authorization.
"""

import uuid
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Depends, status, Header, Query, Response, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..shared.models import BaseResponse
from ..shared.exceptions import ValidationError, ConflictError, NotFoundError, AuthenticationError, DatabaseError
from .schemas import (
    LoginRequest, RegisterRequest, LoginResponse, UserResponse,
    RefreshTokenRequest, RefreshResponse, UserProfileUpdate,
    ChangePasswordRequest, UserInvitationRequest, PasswordResetRequest,
    PasswordResetConfirm
)
from .service import AuthService
from .jwt_handler import jwt_handler

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


async def get_current_user_dependency(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """Dependency to get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        auth_service = AuthService()
        return await auth_service.get_current_user(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    registration_data: RegisterRequest,
    tenant_id: Optional[uuid.UUID] = Query(None, description="Tenant ID for direct registration")
) -> UserResponse:
    """Register a new user with local authentication."""
    try:
        auth_service = AuthService()
        user = await auth_service.register_user(registration_data, tenant_id)
        return user

    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@auth_router.post("/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False)
) -> LoginResponse:
    """Authenticate user with email and password."""
    try:
        # Create LoginRequest from form data
        login_data = LoginRequest(
            email=email,
            password=password,
            remember_me=remember_me
        )

        auth_service = AuthService()
        login_response = await auth_service.authenticate_user(login_data)

        # Add HX-Redirect header for HTMX to redirect to dashboard
        response.headers["HX-Redirect"] = "/dashboard"

        return login_response

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@auth_router.post("/refresh")
async def refresh_token(refresh_data: RefreshTokenRequest) -> RefreshResponse:
    """Refresh access token using refresh token."""
    try:
        auth_service = AuthService()
        token_data = await auth_service.refresh_token(refresh_data.refresh_token)

        return RefreshResponse(
            success=True,
            message="Token refreshed successfully",
            **token_data
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@auth_router.post("/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_user_dependency),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> BaseResponse:
    """Logout current user."""
    try:
        auth_service = AuthService()
        await auth_service.logout(credentials.credentials)

        return BaseResponse(
            success=True,
            message="Logged out successfully"
        )

    except Exception:
        # Always return success for logout
        return BaseResponse(
            success=True,
            message="Logged out successfully"
        )


@auth_router.post("/logout-all")
async def logout_all_sessions(
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> BaseResponse:
    """Logout user from all sessions."""
    try:
        auth_service = AuthService()
        await auth_service.logout_all_sessions(current_user.id)

        return BaseResponse(
            success=True,
            message="Logged out from all sessions"
        )

    except Exception:
        return BaseResponse(
            success=True,
            message="Logged out from all sessions"
        )


@auth_router.get("/me")
async def get_current_user(
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> UserResponse:
    """Get current authenticated user information."""
    return current_user


@auth_router.put("/me")
async def update_profile(
    update_data: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> UserResponse:
    """Update current user's profile."""
    try:
        auth_service = AuthService()
        return await auth_service.update_profile(current_user.id, update_data)

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@auth_router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> BaseResponse:
    """Change user password."""
    try:
        auth_service = AuthService()
        await auth_service.change_password(current_user.id, password_data)

        return BaseResponse(
            success=True,
            message="Password changed successfully"
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@auth_router.post("/password-reset")
async def request_password_reset(reset_data: PasswordResetRequest) -> BaseResponse:
    """Request password reset token."""
    try:
        auth_service = AuthService()
        reset_token = await auth_service.require_password_reset(reset_data.email)

        # In development, return the token directly
        # In production, this would only send an email
        return BaseResponse(
            success=True,
            message="Password reset instructions sent",
            details={"reset_token": reset_token}  # Remove in production
        )

    except AuthenticationError as e:
        # Always return success to prevent email enumeration
        return BaseResponse(
            success=True,
            message="If the email exists, reset instructions will be sent"
        )




@auth_router.post("/password-reset/confirm")
async def confirm_password_reset(reset_data: PasswordResetConfirm) -> BaseResponse:
    """Confirm password reset with token."""
    try:
        auth_service = AuthService()
        await auth_service.reset_password(reset_data.token, reset_data.new_password)

        return BaseResponse(
            success=True,
            message="Password reset successfully"
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@auth_router.post("/invite")
async def invite_user(
    invitation_data: UserInvitationRequest,
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Invite a new user to the tenant."""
    try:
        # Check if user has permission to invite others
        if current_user.role not in ["tenant_admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to invite users"
            )

        auth_service = AuthService()
        invitation = await auth_service.invite_user(
            inviter_id=current_user.id,
            tenant_id=current_user.tenant_id,
            invitation_data=invitation_data
        )

        return invitation

    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation"
        )


@auth_router.get("/invitation/{token}")
async def verify_invitation(token: str) -> Dict[str, Any]:
    """Verify invitation token and return invitation details."""
    try:
        auth_service = AuthService()
        invitation_data = await auth_service.verify_invitation(token)

        return {
            "valid": True,
            "email": invitation_data["email"],
            "tenant_id": invitation_data["tenant_id"],
            "role": invitation_data["role"]
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )




@auth_router.get("/providers")
async def get_auth_providers() -> Dict[str, Any]:
    """Get available authentication providers."""
    auth_service = AuthService()
    providers = auth_service.get_auth_providers()

    return {
        "providers": providers,
        "local_auth_enabled": auth_service.is_local_auth_enabled()
    }


@auth_router.get("/permissions")
async def get_user_permissions(
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get current user permissions."""
    return {
        "success": True,
        "permissions": {
            "can_manage_users": current_user.role in ["tenant_admin", "super_admin"],
            "can_manage_tenants": current_user.role == "super_admin",
            "can_manage_requirements": True,
            "can_invite_users": current_user.role in ["tenant_admin", "super_admin"],
            "can_delete_users": current_user.role in ["tenant_admin", "super_admin"]
        },
        "role": current_user.role
    }


@auth_router.get("/health")
async def auth_health_check() -> Dict[str, Any]:
    """Authentication service health check."""
    return {
        "status": "healthy",
        "service": "authentication",
        "local_auth": True,
        "external_providers": {
            "azure_ad": False,
            "google": False
        }
    }


# Development endpoints for user management

@auth_router.get("/users", dependencies=[Depends(get_current_user_dependency)])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """List users in current tenant (admin only)."""
    try:
        # Check admin permissions
        if current_user.role not in ["tenant_admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        auth_service = AuthService()
        # Use repository directly for listing
        skip = (page - 1) * page_size
        users, total = await auth_service.user_repo.list_users(
            tenant_id=current_user.tenant_id,
            skip=skip,
            limit=page_size,
            search=search
        )

        user_responses = [UserResponse.model_validate(user) for user in users]

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "users": user_responses,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@auth_router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user_dependency)
) -> BaseResponse:
    """Delete a user (admin only)."""
    try:
        # Check admin permissions
        if current_user.role not in ["tenant_admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        auth_service = AuthService()
        success = await auth_service.user_repo.delete_user(user_id, soft_delete=True)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return BaseResponse(
            success=True,
            message="User deleted successfully"
        )

    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
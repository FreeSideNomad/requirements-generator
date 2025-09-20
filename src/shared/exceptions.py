"""
Custom exception classes for the Requirements Generator application.
Provides structured error handling with proper HTTP status codes.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception with structured error information."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(AppException):
    """Raised when data validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_REQUIRED",
            status_code=401,
        )


class AuthorizationError(AppException):
    """Raised when user lacks permission for an operation."""

    def __init__(self, message: str = "Insufficient permissions", required_permission: str = "") -> None:
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PERMISSIONS",
            status_code=403,
            details={"required_permission": required_permission} if required_permission else {},
        )


class TenantError(AppException):
    """Raised when tenant-related operations fail."""

    def __init__(self, message: str, tenant_id: Optional[str] = None) -> None:
        super().__init__(
            message=message,
            error_code="TENANT_ERROR",
            status_code=400,
            details={"tenant_id": tenant_id} if tenant_id else {},
        )


class ConflictError(AppException):
    """Raised when an operation conflicts with current state."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details,
        )


class RateLimitError(AppException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None) -> None:
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class ExternalServiceError(AppException):
    """Raised when external service calls fail."""

    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=f"{service} service error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, **(details or {})},
        )


class AIServiceError(ExternalServiceError):
    """Raised when AI service calls fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(service="AI", message=message, details=details)


class DatabaseError(AppException):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str = "", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=f"Database {operation} failed: {message}",
            error_code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation, **(details or {})},
        )
"""
Base Pydantic models and shared data structures.
Provides common patterns for validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict, validator


class BaseEntity(BaseModel):
    """Base model for all entities with common fields."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="forbid",
        use_enum_values=True,
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    def model_dump_json_safe(self) -> Dict[str, Any]:
        """Serialize model to JSON-safe dictionary."""
        return self.model_dump(mode="json")


class BaseResponse(BaseModel):
    """Base response model with common response structure."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    success: bool = Field(default=True, description="Indicates if operation was successful")
    message: Optional[str] = Field(default=None, description="Optional response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginatedResponse(BaseResponse):
    """Generic paginated response model."""

    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_previous: bool = Field(description="Whether there are previous pages")

    @validator("total_pages", always=True)
    @classmethod
    def calculate_total_pages(cls, v: int, values: Dict[str, Any]) -> int:
        """Calculate total pages based on total items and page size."""
        total_items = values.get("total_items", 0)
        page_size = values.get("page_size", 1)
        return (total_items + page_size - 1) // page_size if total_items > 0 else 0

    @validator("has_next", always=True)
    @classmethod
    def calculate_has_next(cls, v: bool, values: Dict[str, Any]) -> bool:
        """Calculate if there are more pages."""
        page = values.get("page", 1)
        total_pages = values.get("total_pages", 0)
        return page < total_pages

    @validator("has_previous", always=True)
    @classmethod
    def calculate_has_previous(cls, v: bool, values: Dict[str, Any]) -> bool:
        """Calculate if there are previous pages."""
        page = values.get("page", 1)
        return page > 1


T = TypeVar("T", bound=BaseModel)


class PaginatedListResponse(PaginatedResponse):
    """Paginated response with typed data list."""

    data: List[Any] = Field(default_factory=list, description="List of items")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    model_config = ConfigDict(extra="forbid")

    error: Dict[str, Any] = Field(description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier for tracking")


class HealthCheck(BaseModel):
    """Health check response model."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="Overall health status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Individual service statuses")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional health details")


class APIKeyInfo(BaseModel):
    """API key information model."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="API key name")
    prefix: str = Field(description="Key prefix for identification")
    permissions: List[str] = Field(default_factory=list, description="Granted permissions")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp")
    last_used: Optional[datetime] = Field(default=None, description="Last usage timestamp")


class RateLimitInfo(BaseModel):
    """Rate limit information model."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(description="Request limit")
    remaining: int = Field(description="Remaining requests")
    reset_time: datetime = Field(description="Reset timestamp")
    window_seconds: int = Field(description="Window duration in seconds")


class SearchQuery(BaseModel):
    """Generic search query model."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=500, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class BulkOperation(BaseModel):
    """Bulk operation request model."""

    model_config = ConfigDict(extra="forbid")

    action: str = Field(description="Operation to perform")
    ids: List[uuid.UUID] = Field(min_length=1, max_length=100, description="Entity IDs")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Operation parameters")


class BulkOperationResult(BaseModel):
    """Bulk operation result model."""

    model_config = ConfigDict(extra="forbid")

    total_requested: int = Field(description="Total items requested")
    successful: int = Field(description="Successfully processed items")
    failed: int = Field(description="Failed items")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional operation details")
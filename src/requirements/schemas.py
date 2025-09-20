"""
Requirements Pydantic schemas for request/response validation.
Handles projects, requirements, epics, user stories, and acceptance criteria.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, validator

from .models import RequirementType, RequirementStatus, Priority, ComplexityLevel


# Base Schemas
class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    vision: Optional[str] = Field(None, description="Project vision statement")
    goals: Optional[List[str]] = Field(default_factory=list, description="Project goals")
    success_criteria: Optional[List[str]] = Field(default_factory=list, description="Success metrics")
    stakeholders: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Stakeholder info")
    methodology: str = Field(default="agile", description="Development methodology")
    domain_model: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Domain model structure")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    is_template: bool = Field(default=False, description="Whether this is a project template")
    project_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom project settings")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    vision: Optional[str] = None
    goals: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None
    stakeholders: Optional[List[Dict[str, str]]] = None
    methodology: Optional[str] = None
    domain_model: Optional[Dict[str, Any]] = None
    project_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Schema for project responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_by: uuid.UUID
    is_active: bool
    is_template: bool
    project_settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    requirement_count: Optional[int] = Field(None, description="Number of requirements")
    member_count: Optional[int] = Field(None, description="Number of team members")


class ProjectListItem(BaseModel):
    """Schema for project list items."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str]
    methodology: str
    is_active: bool
    is_template: bool
    created_at: datetime
    updated_at: datetime
    requirement_count: int = Field(0, description="Number of requirements")
    member_count: int = Field(0, description="Number of team members")


# Project Member Schemas
class ProjectMemberBase(BaseModel):
    """Base project member schema."""
    role: str = Field(..., description="Member role (owner, admin, contributor, viewer)")
    permissions: Optional[Dict[str, bool]] = Field(default_factory=dict, description="Custom permissions")


class ProjectMemberCreate(ProjectMemberBase):
    """Schema for adding a project member."""
    user_id: uuid.UUID = Field(..., description="User ID to add")


class ProjectMemberUpdate(BaseModel):
    """Schema for updating project member."""
    role: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None
    is_active: Optional[bool] = None


class ProjectMemberResponse(ProjectMemberBase):
    """Schema for project member responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    joined_at: datetime
    invited_by: Optional[uuid.UUID]


# Requirement Schemas
class RequirementBase(BaseModel):
    """Base requirement schema."""
    title: str = Field(..., min_length=1, max_length=500, description="Requirement title")
    description: str = Field(..., min_length=1, description="Requirement description")
    rationale: Optional[str] = Field(None, description="Why this requirement exists")
    requirement_type: RequirementType = Field(..., description="Type of requirement")
    category: Optional[str] = Field(None, max_length=100, description="Custom categorization")
    tags: Optional[List[str]] = Field(default_factory=list, description="Requirement tags")
    priority: Priority = Field(default=Priority.MEDIUM, description="Requirement priority")
    complexity: Optional[ComplexityLevel] = Field(None, description="Development complexity")


class UserStoryFields(BaseModel):
    """User story specific fields."""
    user_persona: Optional[str] = Field(None, max_length=100, description="As a...")
    user_goal: Optional[str] = Field(None, description="I want to...")
    user_benefit: Optional[str] = Field(None, description="So that...")


class RequirementCreate(RequirementBase, UserStoryFields):
    """Schema for creating a new requirement."""
    parent_id: Optional[uuid.UUID] = Field(None, description="Parent requirement ID")
    order_index: int = Field(default=0, description="Order within parent/project")

    # Estimation fields
    story_points: Optional[int] = Field(None, ge=0, le=100, description="Story points estimation")
    estimated_hours: Optional[int] = Field(None, ge=0, description="Estimated development hours")
    business_value: Optional[int] = Field(None, ge=1, le=100, description="Business value score")

    # Dependencies
    depends_on: Optional[List[uuid.UUID]] = Field(default_factory=list, description="Dependency requirement IDs")
    related_requirements: Optional[List[uuid.UUID]] = Field(default_factory=list, description="Related requirement IDs")

    # Domain-driven design
    bounded_context: Optional[str] = Field(None, max_length=100, description="DDD bounded context")
    domain_entity: Optional[str] = Field(None, max_length=100, description="Related domain entity")
    aggregate_root: Optional[str] = Field(None, max_length=100, description="DDD aggregate root")

    # Metadata
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom fields")
    source: Optional[str] = Field(None, max_length=100, description="Requirement source")

    # AI generation context
    ai_generated: bool = Field(default=False, description="Whether AI-generated")
    ai_conversation_id: Optional[uuid.UUID] = Field(None, description="Source AI conversation")
    generation_prompt: Optional[str] = Field(None, description="Original generation prompt")


class RequirementUpdate(BaseModel):
    """Schema for updating a requirement."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    rationale: Optional[str] = None
    requirement_type: Optional[RequirementType] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    status: Optional[RequirementStatus] = None
    priority: Optional[Priority] = None
    complexity: Optional[ComplexityLevel] = None

    # User story fields
    user_persona: Optional[str] = Field(None, max_length=100)
    user_goal: Optional[str] = None
    user_benefit: Optional[str] = None

    # Estimation
    story_points: Optional[int] = Field(None, ge=0, le=100)
    estimated_hours: Optional[int] = Field(None, ge=0)
    business_value: Optional[int] = Field(None, ge=1, le=100)

    # Dependencies
    depends_on: Optional[List[uuid.UUID]] = None
    related_requirements: Optional[List[uuid.UUID]] = None

    # Domain context
    bounded_context: Optional[str] = Field(None, max_length=100)
    domain_entity: Optional[str] = Field(None, max_length=100)
    aggregate_root: Optional[str] = Field(None, max_length=100)

    # Metadata
    custom_fields: Optional[Dict[str, Any]] = None
    source: Optional[str] = Field(None, max_length=100)

    # Version control
    change_reason: Optional[str] = Field(None, description="Reason for this change")


class RequirementResponse(RequirementBase, UserStoryFields):
    """Schema for requirement responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    identifier: str
    order_index: int
    status: RequirementStatus

    # Estimation fields
    story_points: Optional[int]
    estimated_hours: Optional[int]
    business_value: Optional[int]

    # Dependencies
    depends_on: List[uuid.UUID]
    related_requirements: List[uuid.UUID]

    # Domain context
    bounded_context: Optional[str]
    domain_entity: Optional[str]
    aggregate_root: Optional[str]

    # Approval
    approved_by: Optional[uuid.UUID]
    approved_at: Optional[datetime]
    review_notes: Optional[str]

    # AI context
    ai_generated: bool
    ai_conversation_id: Optional[uuid.UUID]
    generation_prompt: Optional[str]

    # Version control
    version: int
    previous_version_id: Optional[uuid.UUID]
    change_reason: Optional[str]

    # Metadata
    custom_fields: Dict[str, Any]
    source: Optional[str]

    # Timestamps and users
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    updated_by: Optional[uuid.UUID]

    # Child requirements count
    children_count: Optional[int] = Field(None, description="Number of child requirements")
    acceptance_criteria_count: Optional[int] = Field(None, description="Number of acceptance criteria")


class RequirementListItem(BaseModel):
    """Schema for requirement list items."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    identifier: str
    title: str
    requirement_type: RequirementType
    status: RequirementStatus
    priority: Priority
    complexity: Optional[ComplexityLevel]
    parent_id: Optional[uuid.UUID]
    story_points: Optional[int]
    business_value: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    children_count: int = Field(0, description="Number of child requirements")
    acceptance_criteria_count: int = Field(0, description="Number of acceptance criteria")


# Acceptance Criteria Schemas
class AcceptanceCriteriaBase(BaseModel):
    """Base acceptance criteria schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Criteria title")
    description: str = Field(..., min_length=1, description="Criteria description")
    given_when_then: Optional[str] = Field(None, description="Gherkin-style format")
    order_index: int = Field(default=0, description="Order within requirement")
    is_testable: bool = Field(default=True, description="Whether this criteria is testable")


class AcceptanceCriteriaCreate(AcceptanceCriteriaBase):
    """Schema for creating acceptance criteria."""
    pass


class AcceptanceCriteriaUpdate(BaseModel):
    """Schema for updating acceptance criteria."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    given_when_then: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_testable: Optional[bool] = None
    test_status: Optional[str] = Field(None, description="Test status: pending, pass, fail")
    test_notes: Optional[str] = Field(None, description="Test execution notes")


class AcceptanceCriteriaResponse(AcceptanceCriteriaBase):
    """Schema for acceptance criteria responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requirement_id: uuid.UUID
    test_status: Optional[str]
    test_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID


# Comment Schemas
class RequirementCommentBase(BaseModel):
    """Base comment schema."""
    content: str = Field(..., min_length=1, description="Comment content")
    comment_type: str = Field(default="comment", description="Type: comment, question, suggestion, objection")


class RequirementCommentCreate(RequirementCommentBase):
    """Schema for creating a comment."""
    parent_comment_id: Optional[uuid.UUID] = Field(None, description="Parent comment for threading")


class RequirementCommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: Optional[str] = Field(None, min_length=1)
    is_resolved: Optional[bool] = None


class RequirementCommentResponse(RequirementCommentBase):
    """Schema for comment responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requirement_id: uuid.UUID
    parent_comment_id: Optional[uuid.UUID]
    is_resolved: bool
    resolved_by: Optional[uuid.UUID]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    replies_count: Optional[int] = Field(None, description="Number of replies")


# Template Schemas
class RequirementTemplateBase(BaseModel):
    """Base requirement template schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    requirement_type: RequirementType = Field(..., description="Type of requirement")
    title_template: str = Field(..., min_length=1, max_length=500, description="Title template")
    description_template: str = Field(..., min_length=1, description="Description template")
    acceptance_criteria_templates: Optional[List[str]] = Field(default_factory=list, description="AC templates")
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom field definitions")
    default_values: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Default field values")


class RequirementTemplateCreate(RequirementTemplateBase):
    """Schema for creating requirement template."""
    is_public: bool = Field(default=False, description="Whether template is public")


class RequirementTemplateUpdate(BaseModel):
    """Schema for updating requirement template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    title_template: Optional[str] = Field(None, min_length=1, max_length=500)
    description_template: Optional[str] = Field(None, min_length=1)
    acceptance_criteria_templates: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    default_values: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class RequirementTemplateResponse(RequirementTemplateBase):
    """Schema for requirement template responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    is_public: bool
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


# Search and Filtering
class RequirementFilter(BaseModel):
    """Schema for requirement filtering."""
    requirement_type: Optional[RequirementType] = None
    status: Optional[RequirementStatus] = None
    priority: Optional[Priority] = None
    complexity: Optional[ComplexityLevel] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search_query: Optional[str] = Field(None, description="Search in title and description")
    tags: Optional[List[str]] = None
    bounded_context: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    has_dependencies: Optional[bool] = None
    is_ai_generated: Optional[bool] = None

    @validator('search_query')
    def validate_search_query(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('Search query must be at least 2 characters')
        return v.strip() if v else None


class PaginatedRequirementResponse(BaseModel):
    """Paginated requirement response."""
    items: List[RequirementListItem]
    total: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    pages: int
    has_next: bool
    has_previous: bool


class PaginatedProjectResponse(BaseModel):
    """Paginated project response."""
    items: List[ProjectListItem]
    total: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    pages: int
    has_next: bool
    has_previous: bool


# Bulk Operations
class RequirementBulkOperation(BaseModel):
    """Schema for bulk operations on requirements."""
    requirement_ids: List[uuid.UUID] = Field(..., min_items=1)
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Import/Export
class RequirementExportFormat(BaseModel):
    """Schema for requirement export configuration."""
    format_type: str = Field(..., description="Export format: markdown, json, csv")
    include_children: bool = Field(default=True, description="Include child requirements")
    include_acceptance_criteria: bool = Field(default=True, description="Include acceptance criteria")
    include_comments: bool = Field(default=False, description="Include comments")
    template: Optional[str] = Field(None, description="Custom template for export")


# Analytics
class RequirementAnalytics(BaseModel):
    """Schema for requirement analytics."""
    total_requirements: int
    requirements_by_type: Dict[str, int]
    requirements_by_status: Dict[str, int]
    requirements_by_priority: Dict[str, int]
    average_story_points: Optional[float]
    completion_rate: float
    ai_generated_percentage: float
    requirements_trends: List[Dict[str, Any]]
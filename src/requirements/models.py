"""
Requirements domain models using SQLAlchemy.
Implements domain-driven design with requirements, epics, user stories, and acceptance criteria.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..shared.models import BaseEntity

Base = declarative_base()


class RequirementType(str, Enum):
    """Type of requirement."""
    EPIC = "epic"
    USER_STORY = "user_story"
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS_RULE = "business_rule"
    CONSTRAINT = "constraint"
    ASSUMPTION = "assumption"


class RequirementStatus(str, Enum):
    """Requirement lifecycle status."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class Priority(str, Enum):
    """Requirement priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NICE_TO_HAVE = "nice_to_have"


class ComplexityLevel(str, Enum):
    """Development complexity estimation."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class Project(Base):
    """Project containing requirements and domain models."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Tenant and ownership
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Project metadata
    vision = Column(Text, nullable=True)  # Project vision statement
    goals = Column(JSON, nullable=True)  # List of project goals
    success_criteria = Column(JSON, nullable=True)  # Success metrics
    stakeholders = Column(JSON, nullable=True)  # Stakeholder information

    # Project settings
    methodology = Column(String(50), nullable=False, default="agile")  # agile, waterfall, etc.
    domain_model = Column(JSON, nullable=True)  # Domain model structure
    project_settings = Column(JSON, nullable=True)  # Custom project settings

    # Status and lifecycle
    is_active = Column(Boolean, nullable=False, default=True)
    is_template = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.id}: {self.name}>"


class ProjectMember(Base):
    """Project team members and their roles."""

    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Role and permissions
    role = Column(String(50), nullable=False)  # owner, admin, contributor, viewer
    permissions = Column(JSON, nullable=True)  # Custom permissions

    # Metadata
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    project = relationship("Project", back_populates="members")

    def __repr__(self):
        return f"<ProjectMember {self.user_id} in {self.project_id}>"


class Requirement(Base):
    """Core requirement entity with hierarchical structure."""

    __tablename__ = "requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Hierarchical structure
    parent_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)  # Order within parent/project

    # Basic information
    identifier = Column(String(50), nullable=False)  # REQ-001, EPIC-001, US-001, etc.
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)  # Why this requirement exists

    # Classification
    requirement_type = Column(String(20), nullable=False)
    category = Column(String(100), nullable=True)  # Custom categorization
    tags = Column(JSON, nullable=True)  # Array of tags

    # Status and lifecycle
    status = Column(String(20), nullable=False, default=RequirementStatus.DRAFT)
    priority = Column(String(20), nullable=False, default=Priority.MEDIUM)
    complexity = Column(String(20), nullable=True)  # Development complexity

    # User story specific fields
    user_persona = Column(String(100), nullable=True)  # "As a..."
    user_goal = Column(Text, nullable=True)  # "I want to..."
    user_benefit = Column(Text, nullable=True)  # "So that..."

    # Estimation and planning
    story_points = Column(Integer, nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    business_value = Column(Integer, nullable=True)  # 1-100 scale

    # Dependencies and relationships
    depends_on = Column(JSON, nullable=True)  # Array of requirement IDs
    related_requirements = Column(JSON, nullable=True)  # Related requirement IDs

    # Domain-driven design context
    bounded_context = Column(String(100), nullable=True)  # DDD bounded context
    domain_entity = Column(String(100), nullable=True)  # Related domain entity
    aggregate_root = Column(String(100), nullable=True)  # DDD aggregate root

    # Approval and validation
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # AI-generated content tracking
    ai_generated = Column(Boolean, nullable=False, default=False)
    ai_conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    generation_prompt = Column(Text, nullable=True)  # Original prompt used

    # Version control
    version = Column(Integer, nullable=False, default=1)
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=True)
    change_reason = Column(Text, nullable=True)

    # Metadata
    custom_fields = Column(JSON, nullable=True)  # Extensible custom fields
    source = Column(String(100), nullable=True)  # Source of requirement (stakeholder, analysis, etc.)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="requirements")
    children = relationship("Requirement", backref="parent", remote_side=[id])
    acceptance_criteria = relationship("AcceptanceCriteria", back_populates="requirement", cascade="all, delete-orphan")
    comments = relationship("RequirementComment", back_populates="requirement", cascade="all, delete-orphan")
    attachments = relationship("RequirementAttachment", back_populates="requirement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Requirement {self.identifier}: {self.title[:50]}>"


class AcceptanceCriteria(Base):
    """Acceptance criteria for requirements (especially user stories)."""

    __tablename__ = "acceptance_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False)

    # Criteria content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    given_when_then = Column(Text, nullable=True)  # Gherkin-style format

    # Organization
    order_index = Column(Integer, nullable=False, default=0)

    # Status
    is_testable = Column(Boolean, nullable=False, default=True)
    test_status = Column(String(20), nullable=True)  # pending, pass, fail
    test_notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    requirement = relationship("Requirement", back_populates="acceptance_criteria")

    def __repr__(self):
        return f"<AcceptanceCriteria {self.id}: {self.title[:30]}>"


class RequirementComment(Base):
    """Comments and discussions on requirements."""

    __tablename__ = "requirement_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False)

    # Comment content
    content = Column(Text, nullable=False)
    comment_type = Column(String(20), nullable=False, default="comment")  # comment, question, suggestion, objection

    # Threading
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("requirement_comments.id"), nullable=True)

    # Status
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    requirement = relationship("Requirement", back_populates="comments")
    replies = relationship("RequirementComment", backref="parent_comment", remote_side=[id])

    def __repr__(self):
        return f"<RequirementComment {self.id} on {self.requirement_id}>"


class RequirementAttachment(Base):
    """File attachments for requirements."""

    __tablename__ = "requirement_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False)

    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Storage path
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)

    # Metadata
    description = Column(Text, nullable=True)
    attachment_type = Column(String(50), nullable=True)  # wireframe, mockup, document, etc.

    # Upload info
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    requirement = relationship("Requirement", back_populates="attachments")

    def __repr__(self):
        return f"<RequirementAttachment {self.filename}>"


class RequirementTemplate(Base):
    """Templates for creating standardized requirements."""

    __tablename__ = "requirement_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    requirement_type = Column(String(20), nullable=False)

    # Template content
    title_template = Column(String(500), nullable=False)
    description_template = Column(Text, nullable=False)
    acceptance_criteria_templates = Column(JSON, nullable=True)  # Array of AC templates

    # Configuration
    custom_fields = Column(JSON, nullable=True)  # Additional field definitions
    default_values = Column(JSON, nullable=True)  # Default field values

    # Scope
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # Null for global
    is_public = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<RequirementTemplate {self.name}>"
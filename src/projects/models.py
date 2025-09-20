"""
Project and requirements domain models.
Core entities for managing requirements gathering projects.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..shared.database import Base


class ProjectStatus(str, Enum):
    """Project lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class ProjectType(str, Enum):
    """Project categorization."""
    FEATURE = "feature"
    EPIC = "epic"
    BUG_FIX = "bug_fix"
    ENHANCEMENT = "enhancement"
    RESEARCH = "research"
    COMPLIANCE = "compliance"


class Priority(str, Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Project(Base):
    """
    Core project model for requirements gathering.
    Projects contain requirements and are scoped within tenants.
    """
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic project information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    key: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "PROJ-001"

    # Multi-tenant relationship
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False
    )

    # Project classification
    project_type: Mapped[ProjectType] = mapped_column(String(20), default=ProjectType.FEATURE)
    status: Mapped[ProjectStatus] = mapped_column(String(20), default=ProjectStatus.DRAFT)
    priority: Mapped[Priority] = mapped_column(String(20), default=Priority.MEDIUM)

    # Project ownership and team
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    # Industry template and configuration
    template_id: Mapped[Optional[str]] = mapped_column(String(100))
    template_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Project goals and success criteria
    objectives: Mapped[List[str]] = mapped_column(JSON, default=list)
    success_criteria: Mapped[List[str]] = mapped_column(JSON, default=list)
    assumptions: Mapped[List[str]] = mapped_column(JSON, default=list)
    constraints: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Business context
    business_value: Mapped[Optional[str]] = mapped_column(Text)
    target_audience: Mapped[Optional[str]] = mapped_column(Text)
    estimated_effort: Mapped[Optional[str]] = mapped_column(String(50))  # e.g., "3 months"

    # Progress tracking
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    requirements_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_requirements_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    target_completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="projects")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    requirements: Mapped[List["Requirement"]] = relationship("Requirement", back_populates="project")
    team_members: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="project")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', key='{self.key}', status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if project is in active development."""
        return self.status in [ProjectStatus.ACTIVE, ProjectStatus.REVIEW]

    @property
    def display_name(self) -> str:
        """Get display name with key prefix."""
        return f"[{self.key}] {self.name}"

    def update_progress(self) -> None:
        """Update completion percentage based on approved requirements."""
        if self.requirements_count > 0:
            self.completion_percentage = int(
                (self.approved_requirements_count / self.requirements_count) * 100
            )
        else:
            self.completion_percentage = 0


class ProjectMember(Base):
    """
    Project team membership with role-based access.
    Defines who can access and modify project requirements.
    """
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    # Role within the project
    role: Mapped[str] = mapped_column(String(50), default="contributor")  # owner, contributor, reviewer, observer
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Membership lifecycle
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="team_members")
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"


class Requirement(Base):
    """
    Individual requirement within a project.
    Core entity for capturing and managing requirements.
    """
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic requirement information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    key: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "REQ-001"

    # Project relationship
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False
    )

    # Requirement classification
    requirement_type: Mapped[str] = mapped_column(String(50), default="functional")
    category: Mapped[Optional[str]] = mapped_column(String(100))
    priority: Mapped[Priority] = mapped_column(String(20), default=Priority.MEDIUM)

    # Requirement details
    acceptance_criteria: Mapped[List[str]] = mapped_column(JSON, default=list)
    business_rules: Mapped[List[str]] = mapped_column(JSON, default=list)
    assumptions: Mapped[List[str]] = mapped_column(JSON, default=list)
    dependencies: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Status and lifecycle
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    # Ownership and review
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id")
    )

    # AI-generated content tracking
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence_score: Mapped[Optional[float]] = mapped_column()
    ai_suggestions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="requirements")
    author: Mapped["User"] = relationship("User", foreign_keys=[author_id])
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id])
    comments: Mapped[List["RequirementComment"]] = relationship("RequirementComment", back_populates="requirement")

    def __repr__(self) -> str:
        return f"<Requirement(id={self.id}, key='{self.key}', title='{self.title}', status='{self.status}')>"

    @property
    def display_name(self) -> str:
        """Get display name with key prefix."""
        return f"[{self.key}] {self.title}"


class RequirementComment(Base):
    """
    Comments and discussions on requirements.
    Supports collaborative requirement refinement.
    """
    __tablename__ = "requirement_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id"),
        nullable=False
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    # Comment content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    comment_type: Mapped[str] = mapped_column(String(20), default="comment")  # comment, suggestion, approval, concern

    # Comment threading
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirement_comments.id")
    )

    # Status
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="comments")
    author: Mapped["User"] = relationship("User")
    parent: Mapped[Optional["RequirementComment"]] = relationship("RequirementComment", remote_side=[id])
    replies: Mapped[List["RequirementComment"]] = relationship("RequirementComment", back_populates="parent")

    def __repr__(self) -> str:
        return f"<RequirementComment(id={self.id}, requirement_id={self.requirement_id}, type='{self.comment_type}')>"
"""
Unit tests for requirements Pydantic schemas.
Tests validation, serialization, and schema behavior.
"""

import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError

from src.requirements.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    RequirementCreate, RequirementUpdate, RequirementResponse,
    AcceptanceCriteriaCreate, AcceptanceCriteriaUpdate, AcceptanceCriteriaResponse,
    RequirementCommentCreate, RequirementCommentResponse,
    RequirementTemplateCreate, RequirementTemplateResponse,
    RequirementFilter, PaginatedRequirementResponse,
    RequirementExportFormat, RequirementAnalytics
)
from src.requirements.models import RequirementType, RequirementStatus, Priority, ComplexityLevel


class TestProjectSchemas:
    """Test project-related schemas."""

    def test_project_create_valid(self):
        """Test valid ProjectCreate schema."""
        data = {
            "name": "Test Project",
            "description": "A test project",
            "vision": "To test schemas",
            "goals": ["Goal 1", "Goal 2"],
            "success_criteria": ["Criteria 1"],
            "stakeholders": [{"name": "John", "role": "PO"}],
            "methodology": "scrum",
            "domain_model": {"contexts": ["user"]},
            "is_template": False,
            "project_settings": {"feature_flags": {"ai_enabled": True}}
        }

        schema = ProjectCreate(**data)
        assert schema.name == "Test Project"
        assert schema.description == "A test project"
        assert schema.vision == "To test schemas"
        assert schema.goals == ["Goal 1", "Goal 2"]
        assert schema.success_criteria == ["Criteria 1"]
        assert schema.stakeholders == [{"name": "John", "role": "PO"}]
        assert schema.methodology == "scrum"
        assert schema.domain_model == {"contexts": ["user"]}
        assert schema.is_template is False
        assert schema.project_settings == {"feature_flags": {"ai_enabled": True}}

    def test_project_create_minimal(self):
        """Test minimal ProjectCreate schema."""
        data = {"name": "Minimal Project"}
        schema = ProjectCreate(**data)

        assert schema.name == "Minimal Project"
        assert schema.description is None
        assert schema.vision is None
        assert schema.goals == []
        assert schema.success_criteria == []
        assert schema.stakeholders == []
        assert schema.methodology == "agile"
        assert schema.domain_model == {}
        assert schema.is_template is False
        assert schema.project_settings == {}

    def test_project_create_invalid_name(self):
        """Test ProjectCreate with invalid name."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"
        assert "name" in str(errors[0]["loc"])

    def test_project_update_partial(self):
        """Test ProjectUpdate with partial data."""
        data = {
            "name": "Updated Project",
            "methodology": "kanban"
        }

        schema = ProjectUpdate(**data)
        assert schema.name == "Updated Project"
        assert schema.methodology == "kanban"
        assert schema.description is None
        assert schema.vision is None

    def test_project_response_from_dict(self):
        """Test ProjectResponse creation from dict."""
        data = {
            "id": str(uuid.uuid4()),
            "name": "Test Project",
            "description": "Test description",
            "vision": "Test vision",
            "goals": ["Goal 1"],
            "success_criteria": ["Criteria 1"],
            "stakeholders": [],
            "methodology": "agile",
            "domain_model": {},
            "tenant_id": str(uuid.uuid4()),
            "created_by": str(uuid.uuid4()),
            "is_active": True,
            "is_template": False,
            "project_settings": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "requirement_count": 5,
            "member_count": 3
        }

        schema = ProjectResponse(**data)
        assert schema.name == "Test Project"
        assert schema.requirement_count == 5
        assert schema.member_count == 3


class TestRequirementSchemas:
    """Test requirement-related schemas."""

    def test_requirement_create_valid(self):
        """Test valid RequirementCreate schema."""
        data = {
            "title": "User Login",
            "description": "User can log into the system",
            "rationale": "Authentication is required",
            "requirement_type": RequirementType.USER_STORY,
            "category": "Authentication",
            "tags": ["login", "auth"],
            "priority": Priority.HIGH,
            "complexity": ComplexityLevel.MODERATE,
            "user_persona": "End User",
            "user_goal": "log into the system",
            "user_benefit": "access my account",
            "story_points": 5,
            "estimated_hours": 16,
            "business_value": 80,
            "depends_on": [str(uuid.uuid4())],
            "related_requirements": [str(uuid.uuid4())],
            "bounded_context": "User Management",
            "domain_entity": "User",
            "aggregate_root": "UserAccount",
            "custom_fields": {"priority_reason": "Critical"},
            "source": "Stakeholder",
            "ai_generated": True
        }

        schema = RequirementCreate(**data)
        assert schema.title == "User Login"
        assert schema.description == "User can log into the system"
        assert schema.requirement_type == RequirementType.USER_STORY
        assert schema.priority == Priority.HIGH
        assert schema.complexity == ComplexityLevel.MODERATE
        assert schema.user_persona == "End User"
        assert schema.story_points == 5
        assert schema.business_value == 80
        assert len(schema.depends_on) == 1
        assert schema.bounded_context == "User Management"
        assert schema.ai_generated is True

    def test_requirement_create_minimal(self):
        """Test minimal RequirementCreate schema."""
        data = {
            "title": "Basic Requirement",
            "description": "Basic description",
            "requirement_type": RequirementType.FUNCTIONAL
        }

        schema = RequirementCreate(**data)
        assert schema.title == "Basic Requirement"
        assert schema.description == "Basic description"
        assert schema.requirement_type == RequirementType.FUNCTIONAL
        assert schema.priority == Priority.MEDIUM
        assert schema.order_index == 0
        assert schema.tags == []
        assert schema.depends_on == []
        assert schema.custom_fields == {}
        assert schema.ai_generated is False

    def test_requirement_create_invalid_title(self):
        """Test RequirementCreate with invalid title."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementCreate(
                title="",
                description="Valid description",
                requirement_type=RequirementType.FUNCTIONAL
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"

    def test_requirement_create_invalid_story_points(self):
        """Test RequirementCreate with invalid story points."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementCreate(
                title="Valid Title",
                description="Valid description",
                requirement_type=RequirementType.USER_STORY,
                story_points=150  # Too high
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "less_than_equal"

    def test_requirement_create_invalid_business_value(self):
        """Test RequirementCreate with invalid business value."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementCreate(
                title="Valid Title",
                description="Valid description",
                requirement_type=RequirementType.FUNCTIONAL,
                business_value=0  # Too low
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "greater_than_equal"

    def test_requirement_update_partial(self):
        """Test RequirementUpdate with partial data."""
        data = {
            "title": "Updated Title",
            "status": RequirementStatus.APPROVED,
            "story_points": 8
        }

        schema = RequirementUpdate(**data)
        assert schema.title == "Updated Title"
        assert schema.status == RequirementStatus.APPROVED
        assert schema.story_points == 8
        assert schema.description is None
        assert schema.priority is None

    def test_requirement_response_from_dict(self):
        """Test RequirementResponse creation from dict."""
        data = {
            "id": str(uuid.uuid4()),
            "project_id": str(uuid.uuid4()),
            "parent_id": None,
            "identifier": "US-001",
            "order_index": 1,
            "title": "User Login",
            "description": "User login functionality",
            "rationale": "Authentication needed",
            "requirement_type": RequirementType.USER_STORY,
            "category": "Auth",
            "tags": ["login"],
            "status": RequirementStatus.DRAFT,
            "priority": Priority.HIGH,
            "complexity": ComplexityLevel.MODERATE,
            "user_persona": "User",
            "user_goal": "login",
            "user_benefit": "access account",
            "story_points": 5,
            "estimated_hours": 16,
            "business_value": 80,
            "depends_on": [],
            "related_requirements": [],
            "bounded_context": "User",
            "domain_entity": "User",
            "aggregate_root": "UserAccount",
            "approved_by": None,
            "approved_at": None,
            "review_notes": None,
            "ai_generated": False,
            "ai_conversation_id": None,
            "generation_prompt": None,
            "version": 1,
            "previous_version_id": None,
            "change_reason": None,
            "custom_fields": {},
            "source": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": str(uuid.uuid4()),
            "updated_by": None,
            "children_count": 0,
            "acceptance_criteria_count": 2
        }

        schema = RequirementResponse(**data)
        assert schema.identifier == "US-001"
        assert schema.title == "User Login"
        assert schema.children_count == 0
        assert schema.acceptance_criteria_count == 2


class TestAcceptanceCriteriaSchemas:
    """Test acceptance criteria schemas."""

    def test_acceptance_criteria_create_valid(self):
        """Test valid AcceptanceCriteriaCreate schema."""
        data = {
            "title": "Login Success",
            "description": "User should be redirected after login",
            "given_when_then": "Given valid creds, when login, then redirect",
            "order_index": 1,
            "is_testable": True
        }

        schema = AcceptanceCriteriaCreate(**data)
        assert schema.title == "Login Success"
        assert schema.description == "User should be redirected after login"
        assert schema.given_when_then == "Given valid creds, when login, then redirect"
        assert schema.order_index == 1
        assert schema.is_testable is True

    def test_acceptance_criteria_create_minimal(self):
        """Test minimal AcceptanceCriteriaCreate schema."""
        data = {
            "title": "Basic Criteria",
            "description": "Basic description"
        }

        schema = AcceptanceCriteriaCreate(**data)
        assert schema.title == "Basic Criteria"
        assert schema.description == "Basic description"
        assert schema.order_index == 0
        assert schema.is_testable is True

    def test_acceptance_criteria_update_partial(self):
        """Test AcceptanceCriteriaUpdate with partial data."""
        data = {
            "test_status": "pass",
            "test_notes": "All tests passing"
        }

        schema = AcceptanceCriteriaUpdate(**data)
        assert schema.test_status == "pass"
        assert schema.test_notes == "All tests passing"
        assert schema.title is None


class TestRequirementCommentSchemas:
    """Test requirement comment schemas."""

    def test_requirement_comment_create_valid(self):
        """Test valid RequirementCommentCreate schema."""
        data = {
            "content": "This needs clarification",
            "comment_type": "question",
            "parent_comment_id": str(uuid.uuid4())
        }

        schema = RequirementCommentCreate(**data)
        assert schema.content == "This needs clarification"
        assert schema.comment_type == "question"
        assert schema.parent_comment_id is not None

    def test_requirement_comment_create_minimal(self):
        """Test minimal RequirementCommentCreate schema."""
        data = {"content": "Basic comment"}

        schema = RequirementCommentCreate(**data)
        assert schema.content == "Basic comment"
        assert schema.comment_type == "comment"
        assert schema.parent_comment_id is None


class TestRequirementTemplateSchemas:
    """Test requirement template schemas."""

    def test_requirement_template_create_valid(self):
        """Test valid RequirementTemplateCreate schema."""
        data = {
            "name": "User Story Template",
            "description": "Standard user story template",
            "requirement_type": RequirementType.USER_STORY,
            "title_template": "As a {persona}, I want to {goal}",
            "description_template": "As a {persona}, I want {goal} so that {benefit}",
            "acceptance_criteria_templates": ["Given {condition}, when {action}, then {result}"],
            "custom_fields": {"persona": "text"},
            "default_values": {"priority": "medium"},
            "is_public": True
        }

        schema = RequirementTemplateCreate(**data)
        assert schema.name == "User Story Template"
        assert schema.requirement_type == RequirementType.USER_STORY
        assert schema.title_template == "As a {persona}, I want to {goal}"
        assert len(schema.acceptance_criteria_templates) == 1
        assert schema.is_public is True

    def test_requirement_template_create_minimal(self):
        """Test minimal RequirementTemplateCreate schema."""
        data = {
            "name": "Basic Template",
            "requirement_type": RequirementType.FUNCTIONAL,
            "title_template": "Basic title",
            "description_template": "Basic description"
        }

        schema = RequirementTemplateCreate(**data)
        assert schema.name == "Basic Template"
        assert schema.acceptance_criteria_templates == []
        assert schema.custom_fields == {}
        assert schema.is_public is False


class TestFilterAndUtilitySchemas:
    """Test filtering and utility schemas."""

    def test_requirement_filter_valid(self):
        """Test valid RequirementFilter schema."""
        data = {
            "requirement_type": RequirementType.USER_STORY,
            "status": RequirementStatus.APPROVED,
            "priority": Priority.HIGH,
            "search_query": "login feature",
            "tags": ["auth", "login"],
            "bounded_context": "User Management",
            "has_dependencies": True,
            "is_ai_generated": False
        }

        schema = RequirementFilter(**data)
        assert schema.requirement_type == RequirementType.USER_STORY
        assert schema.status == RequirementStatus.APPROVED
        assert schema.priority == Priority.HIGH
        assert schema.search_query == "login feature"
        assert schema.tags == ["auth", "login"]
        assert schema.bounded_context == "User Management"
        assert schema.has_dependencies is True
        assert schema.is_ai_generated is False

    def test_requirement_filter_search_query_validation(self):
        """Test RequirementFilter search query validation."""
        # Valid search query
        schema = RequirementFilter(search_query="valid search")
        assert schema.search_query == "valid search"

        # Search query too short
        with pytest.raises(ValidationError) as exc_info:
            RequirementFilter(search_query="a")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 2 characters" in errors[0]["msg"]

        # Empty search query should be rejected
        with pytest.raises(ValidationError) as exc_info:
            RequirementFilter(search_query="  ")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 2 characters" in errors[0]["msg"]

    def test_paginated_requirement_response(self):
        """Test PaginatedRequirementResponse schema."""
        data = {
            "items": [],
            "total": 50,
            "page": 2,
            "page_size": 20,
            "pages": 3,
            "has_next": True,
            "has_previous": True
        }

        schema = PaginatedRequirementResponse(**data)
        assert schema.items == []
        assert schema.total == 50
        assert schema.page == 2
        assert schema.page_size == 20
        assert schema.pages == 3
        assert schema.has_next is True
        assert schema.has_previous is True

    def test_requirement_export_format(self):
        """Test RequirementExportFormat schema."""
        data = {
            "format_type": "markdown",
            "include_children": True,
            "include_acceptance_criteria": True,
            "include_comments": False,
            "template": "user_stories"
        }

        schema = RequirementExportFormat(**data)
        assert schema.format_type == "markdown"
        assert schema.include_children is True
        assert schema.include_acceptance_criteria is True
        assert schema.include_comments is False
        assert schema.template == "user_stories"

    def test_requirement_analytics(self):
        """Test RequirementAnalytics schema."""
        data = {
            "total_requirements": 100,
            "requirements_by_type": {"user_story": 60, "epic": 10},
            "requirements_by_status": {"draft": 30, "approved": 70},
            "requirements_by_priority": {"high": 20, "medium": 50, "low": 30},
            "average_story_points": 5.5,
            "completion_rate": 0.75,
            "ai_generated_percentage": 0.4,
            "requirements_trends": [{"date": "2024-01-01", "count": 10}]
        }

        schema = RequirementAnalytics(**data)
        assert schema.total_requirements == 100
        assert schema.requirements_by_type == {"user_story": 60, "epic": 10}
        assert schema.average_story_points == 5.5
        assert schema.completion_rate == 0.75
        assert schema.ai_generated_percentage == 0.4
        assert len(schema.requirements_trends) == 1


class TestSchemaEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_uuid_format(self):
        """Test handling of invalid UUID formats."""
        with pytest.raises(ValidationError):
            RequirementResponse(
                id="not-a-uuid",
                project_id=str(uuid.uuid4()),
                identifier="REQ-001",
                title="Test",
                description="Test",
                requirement_type=RequirementType.FUNCTIONAL,
                tags=[],
                status=RequirementStatus.DRAFT,
                priority=Priority.MEDIUM,
                depends_on=[],
                related_requirements=[],
                custom_fields={},
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=str(uuid.uuid4())
            )

    def test_long_string_validation(self):
        """Test string length validation."""
        # Test max length for project name
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="x" * 256)  # Too long

        errors = exc_info.value.errors()
        assert any("string_too_long" in error["type"] for error in errors)

        # Test max length for requirement title
        with pytest.raises(ValidationError) as exc_info:
            RequirementCreate(
                title="x" * 501,  # Too long
                description="Valid description",
                requirement_type=RequirementType.FUNCTIONAL
            )

        errors = exc_info.value.errors()
        assert any("string_too_long" in error["type"] for error in errors)

    def test_enum_validation(self):
        """Test enum validation."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementCreate(
                title="Valid Title",
                description="Valid description",
                requirement_type="invalid_type"  # Invalid enum value
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "enum" in errors[0]["type"] or "literal_error" in errors[0]["type"]
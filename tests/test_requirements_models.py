"""
Unit tests for requirements domain models.
Tests the Project, Requirement, AcceptanceCriteria, and related models.
"""

import pytest
from src.requirements.models import (
    RequirementType, RequirementStatus, Priority, ComplexityLevel
)


class TestRequirementEnums:
    """Test requirement enumeration values."""

    def test_requirement_type_values(self):
        """Test RequirementType enum values."""
        assert RequirementType.EPIC == "epic"
        assert RequirementType.USER_STORY == "user_story"
        assert RequirementType.FUNCTIONAL == "functional"
        assert RequirementType.NON_FUNCTIONAL == "non_functional"
        assert RequirementType.BUSINESS_RULE == "business_rule"
        assert RequirementType.CONSTRAINT == "constraint"
        assert RequirementType.ASSUMPTION == "assumption"

    def test_requirement_status_values(self):
        """Test RequirementStatus enum values."""
        assert RequirementStatus.DRAFT == "draft"
        assert RequirementStatus.UNDER_REVIEW == "under_review"
        assert RequirementStatus.APPROVED == "approved"
        assert RequirementStatus.IN_DEVELOPMENT == "in_development"
        assert RequirementStatus.TESTING == "testing"
        assert RequirementStatus.COMPLETED == "completed"
        assert RequirementStatus.REJECTED == "rejected"
        assert RequirementStatus.DEPRECATED == "deprecated"

    def test_priority_values(self):
        """Test Priority enum values."""
        assert Priority.CRITICAL == "critical"
        assert Priority.HIGH == "high"
        assert Priority.MEDIUM == "medium"
        assert Priority.LOW == "low"
        assert Priority.NICE_TO_HAVE == "nice_to_have"

    def test_complexity_level_values(self):
        """Test ComplexityLevel enum values."""
        assert ComplexityLevel.TRIVIAL == "trivial"
        assert ComplexityLevel.SIMPLE == "simple"
        assert ComplexityLevel.MODERATE == "moderate"
        assert ComplexityLevel.COMPLEX == "complex"
        assert ComplexityLevel.VERY_COMPLEX == "very_complex"

    def test_enum_inheritance(self):
        """Test that enums inherit from str and Enum properly."""
        assert isinstance(RequirementType.EPIC, str)
        assert isinstance(RequirementStatus.DRAFT, str)
        assert isinstance(Priority.HIGH, str)
        assert isinstance(ComplexityLevel.MODERATE, str)

    def test_enum_values_complete(self):
        """Test that all expected enum values exist."""
        # Test RequirementType has all expected values
        expected_types = {
            "epic", "user_story", "functional", "non_functional",
            "business_rule", "constraint", "assumption"
        }
        actual_types = {item.value for item in RequirementType}
        assert actual_types == expected_types

        # Test RequirementStatus has all expected values
        expected_statuses = {
            "draft", "under_review", "approved", "in_development",
            "testing", "completed", "rejected", "deprecated"
        }
        actual_statuses = {item.value for item in RequirementStatus}
        assert actual_statuses == expected_statuses

        # Test Priority has all expected values
        expected_priorities = {"critical", "high", "medium", "low", "nice_to_have"}
        actual_priorities = {item.value for item in Priority}
        assert actual_priorities == expected_priorities

        # Test ComplexityLevel has all expected values
        expected_complexity = {"trivial", "simple", "moderate", "complex", "very_complex"}
        actual_complexity = {item.value for item in ComplexityLevel}
        assert actual_complexity == expected_complexity


class TestModelTableNames:
    """Test that model table names are correctly defined."""

    def test_table_names_defined(self):
        """Test that all models have proper table names."""
        from src.requirements.models import (
            Project, ProjectMember, Requirement, AcceptanceCriteria,
            RequirementComment, RequirementAttachment, RequirementTemplate
        )

        assert Project.__tablename__ == "projects"
        assert ProjectMember.__tablename__ == "project_members"
        assert Requirement.__tablename__ == "requirements"
        assert AcceptanceCriteria.__tablename__ == "acceptance_criteria"
        assert RequirementComment.__tablename__ == "requirement_comments"
        assert RequirementAttachment.__tablename__ == "requirement_attachments"
        assert RequirementTemplate.__tablename__ == "requirement_templates"


class TestModelRepresentations:
    """Test model string representations without instantiation."""

    def test_model_repr_methods_exist(self):
        """Test that all models have __repr__ methods defined."""
        from src.requirements.models import (
            Project, ProjectMember, Requirement, AcceptanceCriteria,
            RequirementComment, RequirementAttachment, RequirementTemplate
        )

        models = [
            Project, ProjectMember, Requirement, AcceptanceCriteria,
            RequirementComment, RequirementAttachment, RequirementTemplate
        ]

        for model in models:
            assert hasattr(model, '__repr__')
            assert callable(getattr(model, '__repr__'))


class TestModelAttributes:
    """Test that models have expected attributes defined."""

    def test_project_attributes(self):
        """Test Project model has expected attributes."""
        from src.requirements.models import Project

        expected_columns = {
            'id', 'name', 'description', 'tenant_id', 'created_by',
            'vision', 'goals', 'success_criteria', 'stakeholders',
            'methodology', 'domain_model', 'project_settings',
            'is_active', 'is_template', 'created_at', 'updated_at'
        }

        actual_columns = set(Project.__table__.columns.keys())
        assert expected_columns.issubset(actual_columns)

    def test_requirement_attributes(self):
        """Test Requirement model has expected attributes."""
        from src.requirements.models import Requirement

        expected_columns = {
            'id', 'project_id', 'parent_id', 'order_index', 'identifier',
            'title', 'description', 'rationale', 'requirement_type',
            'category', 'tags', 'status', 'priority', 'complexity',
            'user_persona', 'user_goal', 'user_benefit', 'story_points',
            'estimated_hours', 'business_value', 'depends_on',
            'related_requirements', 'bounded_context', 'domain_entity',
            'aggregate_root', 'created_at', 'updated_at', 'created_by'
        }

        actual_columns = set(Requirement.__table__.columns.keys())
        assert expected_columns.issubset(actual_columns)

    def test_acceptance_criteria_attributes(self):
        """Test AcceptanceCriteria model has expected attributes."""
        from src.requirements.models import AcceptanceCriteria

        expected_columns = {
            'id', 'requirement_id', 'title', 'description',
            'given_when_then', 'order_index', 'is_testable',
            'test_status', 'test_notes', 'created_at', 'updated_at', 'created_by'
        }

        actual_columns = set(AcceptanceCriteria.__table__.columns.keys())
        assert expected_columns.issubset(actual_columns)
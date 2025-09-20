"""
Tests for enhanced domain models.
"""

import pytest
import uuid
from src.domain.models.bounded_context import BoundedContext
from src.domain.models.domain_entity import DomainEntity, DefaultDomainEntityValidator
from src.domain.models.aggregate_root import AggregateRoot, DefaultAggregateFactory, AggregateConsistencyValidator
from src.domain.models.value_objects import (
    Priority, PriorityLevel, ComplexityLevel, ComplexityScale,
    BusinessValue, StoryPoints, RequirementIdentifier
)


class TestBoundedContext:
    """Test BoundedContext domain model."""

    def test_bounded_context_creation(self):
        """Test creating a bounded context."""
        context = BoundedContext(
            name="User Management",
            description="Handles user operations",
            ubiquitous_language={"User", "Profile"},
            domain_entities={"User", "Profile"},
            aggregate_roots={"UserAccount"}
        )

        assert context.name == "User Management"
        assert context.description == "Handles user operations"
        assert "User" in context.ubiquitous_language
        assert "User" in context.domain_entities
        assert "UserAccount" in context.aggregate_roots

    def test_bounded_context_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Bounded context name cannot be empty"):
            BoundedContext(name="")

    def test_bounded_context_none_sets_defaults(self):
        """Test that None values get default sets."""
        context = BoundedContext(name="Test Context")

        assert context.ubiquitous_language == set()
        assert context.domain_entities == set()
        assert context.aggregate_roots == set()

    def test_add_domain_entity(self):
        """Test adding domain entity to context."""
        context = BoundedContext(name="Test Context")
        new_context = context.add_domain_entity("TestEntity")

        assert "TestEntity" in new_context.domain_entities
        assert "TestEntity" not in context.domain_entities  # Original unchanged

    def test_add_aggregate_root(self):
        """Test adding aggregate root to context."""
        context = BoundedContext(name="Test Context")
        new_context = context.add_aggregate_root("TestAggregate")

        assert "TestAggregate" in new_context.aggregate_roots

    def test_contains_entity(self):
        """Test checking if context contains entity."""
        context = BoundedContext(
            name="Test Context",
            domain_entities={"User", "Profile"}
        )

        assert context.contains_entity("User")
        assert not context.contains_entity("NonExistent")


class TestDomainEntity:
    """Test DomainEntity domain model."""

    def test_domain_entity_creation(self):
        """Test creating a domain entity."""
        entity_id = str(uuid.uuid4())
        entity = DomainEntity(
            name="User",
            entity_id=entity_id,
            bounded_context="User Management",
            attributes={"email": "string", "name": "string"},
            business_rules=["Email must be unique"],
            invariants=["Email must be valid format"]
        )

        assert entity.name == "User"
        assert entity.entity_id == entity_id
        assert entity.bounded_context == "User Management"
        assert entity.has_attribute("email")
        assert entity.get_attribute("email") == "string"

    def test_domain_entity_validation(self):
        """Test domain entity validation."""
        # Empty name should raise error
        with pytest.raises(ValueError, match="Domain entity name cannot be empty"):
            DomainEntity(
                name="",
                entity_id=str(uuid.uuid4()),
                bounded_context="Test",
                attributes={}
            )

        # Empty entity_id should raise error
        with pytest.raises(ValueError, match="Domain entity ID cannot be empty"):
            DomainEntity(
                name="Test",
                entity_id="",
                bounded_context="Test",
                attributes={}
            )

    def test_add_business_rule(self):
        """Test adding business rule to entity."""
        entity = DomainEntity(
            name="User",
            entity_id=str(uuid.uuid4()),
            bounded_context="Test",
            attributes={}
        )

        new_entity = entity.add_business_rule("Email must be unique")
        assert "Email must be unique" in new_entity.business_rules
        assert len(entity.business_rules) == 0  # Original unchanged

    def test_with_attributes(self):
        """Test updating entity attributes."""
        entity = DomainEntity(
            name="User",
            entity_id=str(uuid.uuid4()),
            bounded_context="Test",
            attributes={"name": "string"}
        )

        new_entity = entity.with_attributes(email="string", age="integer")
        assert new_entity.get_attribute("email") == "string"
        assert new_entity.get_attribute("age") == "integer"
        assert new_entity.get_attribute("name") == "string"  # Original preserved


class TestDomainEntityValidator:
    """Test DomainEntityValidator."""

    def test_valid_entity_passes_validation(self):
        """Test that valid entity passes validation."""
        validator = DefaultDomainEntityValidator()
        entity = DomainEntity(
            name="User",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        errors = validator.validate(entity)
        assert len(errors) == 0

    def test_invalid_entity_id_fails_validation(self):
        """Test that invalid entity ID fails validation."""
        validator = DefaultDomainEntityValidator()
        entity = DomainEntity(
            name="User",
            entity_id="not-a-uuid",
            bounded_context="User Management",
            attributes={}
        )

        errors = validator.validate(entity)
        assert any("valid UUID" in error for error in errors)


class TestValueObjects:
    """Test value objects."""

    def test_priority_creation(self):
        """Test creating Priority value object."""
        priority = Priority(PriorityLevel.HIGH, "Critical for MVP")

        assert priority.level == PriorityLevel.HIGH
        assert priority.reason == "Critical for MVP"
        assert priority.numeric_value == 4
        assert priority.is_higher_than(Priority(PriorityLevel.MEDIUM))

    def test_complexity_level_creation(self):
        """Test creating ComplexityLevel value object."""
        complexity = ComplexityLevel(ComplexityScale.MODERATE, "Standard operations")

        assert complexity.scale == ComplexityScale.MODERATE
        assert complexity.explanation == "Standard operations"
        assert complexity.numeric_value == 3

    def test_business_value_creation(self):
        """Test creating BusinessValue value object."""
        value = BusinessValue(85, "High impact on user experience")

        assert value.score == 85
        assert value.justification == "High impact on user experience"
        assert value.is_high_value
        assert not value.is_medium_value
        assert not value.is_low_value

    def test_business_value_validation(self):
        """Test BusinessValue validation."""
        # Score out of range should raise error
        with pytest.raises(ValueError, match="Business value score must be between 0 and 100"):
            BusinessValue(150)

        with pytest.raises(ValueError, match="Business value score must be between 0 and 100"):
            BusinessValue(-10)

    def test_story_points_creation(self):
        """Test creating StoryPoints value object."""
        points = StoryPoints(8, "Planning poker estimation")

        assert points.points == 8
        assert points.estimation_method == "Planning poker estimation"
        assert not points.is_large_story
        assert not points.is_epic

        # Test large story
        large_points = StoryPoints(21)
        assert large_points.is_large_story
        assert large_points.is_epic

    def test_requirement_identifier_creation(self):
        """Test creating RequirementIdentifier value object."""
        req_id = RequirementIdentifier("REQ", 1, "v1.0")

        assert req_id.prefix == "REQ"
        assert req_id.number == 1
        assert req_id.version == "v1.0"
        assert req_id.full_identifier == "REQ-0001.v1.0"

    def test_requirement_identifier_from_string(self):
        """Test creating RequirementIdentifier from string."""
        req_id = RequirementIdentifier.from_string("USR-0042.v2.1")

        assert req_id.prefix == "USR"
        assert req_id.number == 42
        assert req_id.version == "v2.1"

    def test_requirement_identifier_increment(self):
        """Test incrementing requirement identifier."""
        req_id = RequirementIdentifier("REQ", 5)
        incremented = req_id.increment()

        assert incremented.number == 6
        assert incremented.prefix == "REQ"

    def test_requirement_identifier_comparison(self):
        """Test requirement identifier comparison."""
        req1 = RequirementIdentifier("REQ", 1)
        req2 = RequirementIdentifier("REQ", 2)
        req3 = RequirementIdentifier("USR", 1)

        assert req1 < req2
        assert req1 < req3  # Different prefix, alphabetical order


class TestAggregateRoot:
    """Test AggregateRoot domain model."""

    def test_aggregate_root_creation(self):
        """Test creating an aggregate root."""
        root_entity = DomainEntity(
            name="UserAccount",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        aggregate = AggregateRoot(
            name="UserAccount",
            aggregate_id=str(uuid.uuid4()),
            bounded_context="User Management",
            root_entity=root_entity
        )

        assert aggregate.name == "UserAccount"
        assert aggregate.bounded_context == "User Management"
        assert aggregate.root_entity == root_entity
        assert len(aggregate.child_entities) == 0

    def test_aggregate_root_validation(self):
        """Test aggregate root validation."""
        root_entity = DomainEntity(
            name="UserAccount",
            entity_id=str(uuid.uuid4()),
            bounded_context="Different Context",
            attributes={}
        )

        # Should raise error if root entity has different bounded context
        with pytest.raises(ValueError, match="Root entity must belong to the same bounded context"):
            AggregateRoot(
                name="UserAccount",
                aggregate_id=str(uuid.uuid4()),
                bounded_context="User Management",
                root_entity=root_entity
            )

    def test_add_child_entity(self):
        """Test adding child entity to aggregate."""
        root_entity = DomainEntity(
            name="UserAccount",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        aggregate = AggregateRoot(
            name="UserAccount",
            aggregate_id=str(uuid.uuid4()),
            bounded_context="User Management",
            root_entity=root_entity
        )

        child_entity = DomainEntity(
            name="Profile",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        new_aggregate = aggregate.add_child_entity(child_entity)
        assert len(new_aggregate.child_entities) == 1
        assert child_entity in new_aggregate.child_entities

    def test_get_all_entities(self):
        """Test getting all entities from aggregate."""
        root_entity = DomainEntity(
            name="UserAccount",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        child_entity = DomainEntity(
            name="Profile",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        aggregate = AggregateRoot(
            name="UserAccount",
            aggregate_id=str(uuid.uuid4()),
            bounded_context="User Management",
            root_entity=root_entity,
            child_entities=[child_entity]
        )

        all_entities = aggregate.get_all_entities()
        assert len(all_entities) == 2
        assert root_entity in all_entities
        assert child_entity in all_entities


class TestAggregateFactory:
    """Test AggregateFactory."""

    def test_default_factory_creates_aggregate(self):
        """Test that default factory creates valid aggregate."""
        factory = DefaultAggregateFactory()

        aggregate = factory.create_aggregate(
            name="TestAggregate",
            bounded_context="Test Context",
            root_entity_data={
                "name": "TestRoot",
                "attributes": {"test": "value"},
                "business_rules": ["Test rule"]
            }
        )

        assert aggregate.name == "TestAggregate"
        assert aggregate.bounded_context == "Test Context"
        assert aggregate.root_entity.name == "TestRoot"
        assert aggregate.root_entity.get_attribute("test") == "value"


class TestAggregateConsistencyValidator:
    """Test AggregateConsistencyValidator."""

    def test_valid_aggregate_passes_validation(self):
        """Test that valid aggregate passes consistency validation."""
        validator = AggregateConsistencyValidator()

        root_entity = DomainEntity(
            name="UserAccount",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        aggregate = AggregateRoot(
            name="UserAccount",
            aggregate_id=str(uuid.uuid4()),
            bounded_context="User Management",
            root_entity=root_entity
        )

        errors = validator.validate_consistency(aggregate)
        assert len(errors) == 0

    def test_different_bounded_context_fails_validation(self):
        """Test that entities with different bounded contexts fail validation."""
        validator = AggregateConsistencyValidator()

        root_entity = DomainEntity(
            name="UserAccount",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={}
        )

        # Create child entity with different bounded context
        child_entity = DomainEntity(
            name="Profile",
            entity_id=str(uuid.uuid4()),
            bounded_context="Different Context",  # Different context
            attributes={}
        )

        # Create valid aggregate first, then test validator with child entity in different context
        aggregate = AggregateRoot(
            name="UserAccount",
            aggregate_id=str(uuid.uuid4()),
            bounded_context="User Management",
            root_entity=root_entity,
            child_entities=[],  # Start with empty children
            domain_events=[],
            consistency_rules=[]
        )

        # Manually add child with different context for testing validator
        # We need to bypass the normal validation in add_child_entity
        test_aggregate = AggregateRoot.__new__(AggregateRoot)
        object.__setattr__(test_aggregate, 'name', "UserAccount")
        object.__setattr__(test_aggregate, 'aggregate_id', str(uuid.uuid4()))
        object.__setattr__(test_aggregate, 'bounded_context', "User Management")
        object.__setattr__(test_aggregate, 'root_entity', root_entity)
        object.__setattr__(test_aggregate, 'child_entities', [child_entity])
        object.__setattr__(test_aggregate, 'domain_events', [])
        object.__setattr__(test_aggregate, 'consistency_rules', [])

        errors = validator.validate_consistency(test_aggregate)
        assert len(errors) > 0
        assert any("does not belong to bounded context" in error for error in errors)
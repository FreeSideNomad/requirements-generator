"""
Aggregate Root domain model.
Represents an aggregate root in the domain-driven design model.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any
import uuid
from abc import ABC, abstractmethod
from .domain_entity import DomainEntity


@dataclass(frozen=True)
class AggregateRoot:
    """
    Represents an aggregate root in DDD.
    An aggregate root is the only member of its aggregate that
    can be referenced from outside the aggregate.
    """

    name: str
    aggregate_id: str
    bounded_context: str
    root_entity: DomainEntity
    child_entities: List[DomainEntity] = field(default_factory=list)
    domain_events: List[str] = field(default_factory=list)
    consistency_rules: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate the aggregate root."""
        if not self.name or not self.name.strip():
            raise ValueError("Aggregate root name cannot be empty")

        if not self.aggregate_id or not self.aggregate_id.strip():
            raise ValueError("Aggregate root ID cannot be empty")

        if not self.bounded_context or not self.bounded_context.strip():
            raise ValueError("Bounded context cannot be empty")

        if self.root_entity.bounded_context != self.bounded_context:
            raise ValueError("Root entity must belong to the same bounded context")

        # Validate that all child entities belong to the same bounded context
        for entity in self.child_entities:
            if entity.bounded_context != self.bounded_context:
                raise ValueError(
                    f"Child entity {entity.name} must belong to the same bounded context"
                )

    def add_child_entity(self, entity: DomainEntity) -> 'AggregateRoot':
        """Add a child entity to this aggregate."""
        if entity.bounded_context != self.bounded_context:
            raise ValueError("Child entity must belong to the same bounded context")

        new_children = self.child_entities.copy()
        new_children.append(entity)

        return AggregateRoot(
            name=self.name,
            aggregate_id=self.aggregate_id,
            bounded_context=self.bounded_context,
            root_entity=self.root_entity,
            child_entities=new_children,
            domain_events=self.domain_events,
            consistency_rules=self.consistency_rules
        )

    def add_domain_event(self, event: str) -> 'AggregateRoot':
        """Add a domain event to this aggregate."""
        new_events = self.domain_events.copy()
        new_events.append(event)

        return AggregateRoot(
            name=self.name,
            aggregate_id=self.aggregate_id,
            bounded_context=self.bounded_context,
            root_entity=self.root_entity,
            child_entities=self.child_entities,
            domain_events=new_events,
            consistency_rules=self.consistency_rules
        )

    def add_consistency_rule(self, rule: str) -> 'AggregateRoot':
        """Add a consistency rule to this aggregate."""
        new_rules = self.consistency_rules.copy()
        new_rules.append(rule)

        return AggregateRoot(
            name=self.name,
            aggregate_id=self.aggregate_id,
            bounded_context=self.bounded_context,
            root_entity=self.root_entity,
            child_entities=self.child_entities,
            domain_events=self.domain_events,
            consistency_rules=new_rules
        )

    def get_all_entities(self) -> List[DomainEntity]:
        """Get all entities in this aggregate (root + children)."""
        return [self.root_entity] + self.child_entities

    def has_entity(self, entity_name: str) -> bool:
        """Check if this aggregate contains an entity with the given name."""
        all_entities = self.get_all_entities()
        return any(entity.name == entity_name for entity in all_entities)

    def get_entity_by_name(self, entity_name: str) -> Optional[DomainEntity]:
        """Get an entity by name from this aggregate."""
        all_entities = self.get_all_entities()
        for entity in all_entities:
            if entity.name == entity_name:
                return entity
        return None

    def __str__(self) -> str:
        return f"AggregateRoot({self.name}:{self.aggregate_id})"

    def __repr__(self) -> str:
        return (
            f"AggregateRoot(name='{self.name}', "
            f"id='{self.aggregate_id}', "
            f"context='{self.bounded_context}', "
            f"entities={len(self.child_entities) + 1})"
        )


class AggregateFactory(ABC):
    """Abstract factory for creating aggregates."""

    @abstractmethod
    def create_aggregate(
        self,
        name: str,
        bounded_context: str,
        root_entity_data: Dict[str, Any]
    ) -> AggregateRoot:
        """Create a new aggregate root."""
        pass


class DefaultAggregateFactory(AggregateFactory):
    """Default factory for creating aggregates."""

    def create_aggregate(
        self,
        name: str,
        bounded_context: str,
        root_entity_data: Dict[str, Any]
    ) -> AggregateRoot:
        """Create a new aggregate root with a default root entity."""
        aggregate_id = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())

        root_entity = DomainEntity(
            name=root_entity_data.get("name", name),
            entity_id=entity_id,
            bounded_context=bounded_context,
            attributes=root_entity_data.get("attributes", {}),
            business_rules=root_entity_data.get("business_rules", []),
            invariants=root_entity_data.get("invariants", [])
        )

        return AggregateRoot(
            name=name,
            aggregate_id=aggregate_id,
            bounded_context=bounded_context,
            root_entity=root_entity
        )


class AggregateConsistencyValidator:
    """Validator for aggregate consistency rules."""

    def validate_consistency(self, aggregate: AggregateRoot) -> List[str]:
        """Validate that the aggregate maintains consistency."""
        errors = []

        # Check that all entities belong to the same bounded context
        all_entities = aggregate.get_all_entities()
        for entity in all_entities:
            if entity.bounded_context != aggregate.bounded_context:
                errors.append(
                    f"Entity {entity.name} does not belong to bounded context "
                    f"{aggregate.bounded_context}"
                )

        # Check for duplicate entity names within the aggregate
        entity_names = [entity.name for entity in all_entities]
        duplicates = set([name for name in entity_names if entity_names.count(name) > 1])
        if duplicates:
            errors.append(f"Duplicate entity names found: {duplicates}")

        return errors
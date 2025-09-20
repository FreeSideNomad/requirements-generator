"""
Domain Entity model.
Represents a domain entity in the domain-driven design model.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import uuid
from abc import ABC, abstractmethod


@dataclass(frozen=True)
class DomainEntity:
    """
    Represents a domain entity in DDD.
    A domain entity is an object that is not defined by its attributes,
    but rather by a thread of continuity and its identity.
    """

    name: str
    entity_id: str
    bounded_context: str
    attributes: Dict[str, Any]
    business_rules: Optional[List[str]] = None
    invariants: Optional[List[str]] = None

    def __post_init__(self):
        """Validate the domain entity."""
        if not self.name or not self.name.strip():
            raise ValueError("Domain entity name cannot be empty")

        if not self.entity_id or not self.entity_id.strip():
            raise ValueError("Domain entity ID cannot be empty")

        if not self.bounded_context or not self.bounded_context.strip():
            raise ValueError("Bounded context cannot be empty")

        if self.business_rules is None:
            object.__setattr__(self, 'business_rules', [])

        if self.invariants is None:
            object.__setattr__(self, 'invariants', [])

    def has_attribute(self, attribute_name: str) -> bool:
        """Check if the entity has a specific attribute."""
        return attribute_name in self.attributes

    def get_attribute(self, attribute_name: str) -> Any:
        """Get the value of a specific attribute."""
        return self.attributes.get(attribute_name)

    def add_business_rule(self, rule: str) -> 'DomainEntity':
        """Add a business rule to this entity."""
        new_rules = self.business_rules.copy()
        new_rules.append(rule)

        return DomainEntity(
            name=self.name,
            entity_id=self.entity_id,
            bounded_context=self.bounded_context,
            attributes=self.attributes,
            business_rules=new_rules,
            invariants=self.invariants
        )

    def add_invariant(self, invariant: str) -> 'DomainEntity':
        """Add an invariant to this entity."""
        new_invariants = self.invariants.copy()
        new_invariants.append(invariant)

        return DomainEntity(
            name=self.name,
            entity_id=self.entity_id,
            bounded_context=self.bounded_context,
            attributes=self.attributes,
            business_rules=self.business_rules,
            invariants=new_invariants
        )

    def with_attributes(self, **new_attributes) -> 'DomainEntity':
        """Create a new entity with updated attributes."""
        updated_attributes = self.attributes.copy()
        updated_attributes.update(new_attributes)

        return DomainEntity(
            name=self.name,
            entity_id=self.entity_id,
            bounded_context=self.bounded_context,
            attributes=updated_attributes,
            business_rules=self.business_rules,
            invariants=self.invariants
        )

    def __str__(self) -> str:
        return f"DomainEntity({self.name}:{self.entity_id})"

    def __repr__(self) -> str:
        return (
            f"DomainEntity(name='{self.name}', "
            f"id='{self.entity_id}', "
            f"context='{self.bounded_context}')"
        )


class DomainEntityValidator(ABC):
    """Abstract base class for domain entity validators."""

    @abstractmethod
    def validate(self, entity: DomainEntity) -> List[str]:
        """
        Validate a domain entity and return a list of validation errors.
        Returns an empty list if the entity is valid.
        """
        pass


class DefaultDomainEntityValidator(DomainEntityValidator):
    """Default validator for domain entities."""

    def validate(self, entity: DomainEntity) -> List[str]:
        """Validate a domain entity."""
        errors = []

        if not entity.name.strip():
            errors.append("Entity name cannot be empty")

        if not entity.entity_id.strip():
            errors.append("Entity ID cannot be empty")

        if not entity.bounded_context.strip():
            errors.append("Bounded context cannot be empty")

        # Validate that entity ID is a valid format
        try:
            uuid.UUID(entity.entity_id)
        except ValueError:
            errors.append("Entity ID must be a valid UUID")

        return errors
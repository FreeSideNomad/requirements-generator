"""
Bounded Context domain model.
Represents a bounded context in the domain-driven design model.
"""

from dataclasses import dataclass
from typing import List, Optional, Set
import uuid
from datetime import datetime


@dataclass(frozen=True)
class BoundedContext:
    """
    Represents a bounded context in DDD.
    A bounded context is an explicit boundary within which a domain model exists.
    """

    name: str
    description: Optional[str] = None
    ubiquitous_language: Optional[Set[str]] = None
    domain_entities: Optional[Set[str]] = None
    aggregate_roots: Optional[Set[str]] = None

    def __post_init__(self):
        """Validate the bounded context."""
        if not self.name or not self.name.strip():
            raise ValueError("Bounded context name cannot be empty")

        if self.ubiquitous_language is None:
            object.__setattr__(self, 'ubiquitous_language', set())

        if self.domain_entities is None:
            object.__setattr__(self, 'domain_entities', set())

        if self.aggregate_roots is None:
            object.__setattr__(self, 'aggregate_roots', set())

    def add_domain_entity(self, entity_name: str) -> 'BoundedContext':
        """Add a domain entity to this bounded context."""
        new_entities = self.domain_entities.copy()
        new_entities.add(entity_name)

        return BoundedContext(
            name=self.name,
            description=self.description,
            ubiquitous_language=self.ubiquitous_language,
            domain_entities=new_entities,
            aggregate_roots=self.aggregate_roots
        )

    def add_aggregate_root(self, aggregate_name: str) -> 'BoundedContext':
        """Add an aggregate root to this bounded context."""
        new_aggregates = self.aggregate_roots.copy()
        new_aggregates.add(aggregate_name)

        return BoundedContext(
            name=self.name,
            description=self.description,
            ubiquitous_language=self.ubiquitous_language,
            domain_entities=self.domain_entities,
            aggregate_roots=new_aggregates
        )

    def add_to_ubiquitous_language(self, term: str) -> 'BoundedContext':
        """Add a term to the ubiquitous language."""
        new_language = self.ubiquitous_language.copy()
        new_language.add(term)

        return BoundedContext(
            name=self.name,
            description=self.description,
            ubiquitous_language=new_language,
            domain_entities=self.domain_entities,
            aggregate_roots=self.aggregate_roots
        )

    def contains_entity(self, entity_name: str) -> bool:
        """Check if this bounded context contains a specific domain entity."""
        return entity_name in self.domain_entities

    def contains_aggregate(self, aggregate_name: str) -> bool:
        """Check if this bounded context contains a specific aggregate root."""
        return aggregate_name in self.aggregate_roots

    def __str__(self) -> str:
        return f"BoundedContext({self.name})"

    def __repr__(self) -> str:
        return (
            f"BoundedContext(name='{self.name}', "
            f"entities={len(self.domain_entities)}, "
            f"aggregates={len(self.aggregate_roots)})"
        )
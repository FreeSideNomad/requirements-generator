"""
Domain Services for business logic that doesn't naturally fit within entities or value objects.
Domain services contain business logic that operates on multiple entities or aggregates.
"""

from typing import List, Dict, Any, Optional, Set
import uuid
from abc import ABC, abstractmethod
from .bounded_context import BoundedContext
from .domain_entity import DomainEntity
from .aggregate_root import AggregateRoot
from .value_objects import Priority, ComplexityLevel, BusinessValue, StoryPoints, ComplexityScale


class RequirementDomainService:
    """
    Domain service for requirement-related business logic.
    Handles operations that span multiple requirement entities.
    """

    def calculate_project_complexity(
        self,
        requirements: List[Dict[str, Any]]
    ) -> ComplexityLevel:
        """Calculate overall project complexity based on requirements."""
        if not requirements:
            return ComplexityLevel(ComplexityScale.TRIVIAL)

        # Calculate weighted complexity based on story points and complexity
        total_weighted_complexity = 0
        total_story_points = 0

        for req in requirements:
            complexity_value = req.get('complexity', 1)
            story_points = req.get('story_points', 1)

            total_weighted_complexity += complexity_value * story_points
            total_story_points += story_points

        if total_story_points == 0:
            return ComplexityLevel(ComplexityScale.TRIVIAL)

        average_complexity = total_weighted_complexity / total_story_points

        # Map to complexity scale
        if average_complexity >= 4.5:
            return ComplexityLevel(ComplexityScale.VERY_COMPLEX)
        elif average_complexity >= 3.5:
            return ComplexityLevel(ComplexityScale.COMPLEX)
        elif average_complexity >= 2.5:
            return ComplexityLevel(ComplexityScale.MODERATE)
        elif average_complexity >= 1.5:
            return ComplexityLevel(ComplexityScale.SIMPLE)
        else:
            return ComplexityLevel(ComplexityScale.TRIVIAL)

    def identify_requirement_dependencies(
        self,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Identify potential dependencies between requirements."""
        dependencies = {}

        for req in requirements:
            req_id = req.get('id', '')
            dependencies[req_id] = []

            # Analyze dependencies based on domain entities and bounded contexts
            req_entities = set(req.get('domain_entities', []))
            req_context = req.get('bounded_context', '')

            for other_req in requirements:
                if other_req.get('id') == req_id:
                    continue

                other_entities = set(other_req.get('domain_entities', []))
                other_context = other_req.get('bounded_context', '')

                # Check for entity overlap
                if req_entities.intersection(other_entities):
                    dependencies[req_id].append(other_req.get('id', ''))

                # Check for context relationships
                elif self._are_contexts_related(req_context, other_context):
                    dependencies[req_id].append(other_req.get('id', ''))

        return dependencies

    def _are_contexts_related(self, context1: str, context2: str) -> bool:
        """Determine if two bounded contexts are related."""
        # Simple heuristic - can be made more sophisticated
        known_relationships = {
            ('User Management', 'Authentication'),
            ('Order Processing', 'Payment'),
            ('Inventory', 'Product Catalog'),
            ('Reporting', 'Analytics')
        }

        return (context1, context2) in known_relationships or \
               (context2, context1) in known_relationships

    def prioritize_requirements(
        self,
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize requirements based on business value and dependencies."""
        # Calculate priority scores
        for req in requirements:
            priority_score = self._calculate_priority_score(req)
            req['priority_score'] = priority_score

        # Sort by priority score (higher first)
        return sorted(requirements, key=lambda x: x.get('priority_score', 0), reverse=True)

    def _calculate_priority_score(self, requirement: Dict[str, Any]) -> float:
        """Calculate a priority score for a requirement."""
        business_value = requirement.get('business_value', 50)
        priority_weight = self._get_priority_weight(requirement.get('priority', 'medium'))
        story_points = requirement.get('story_points', 3)

        # Higher business value and priority increase score
        # Lower story points (easier to implement) slightly increase score
        score = (business_value * priority_weight) / (story_points ** 0.5)

        return score

    def _get_priority_weight(self, priority: str) -> float:
        """Get numeric weight for priority level."""
        weights = {
            'critical': 2.0,
            'high': 1.5,
            'medium': 1.0,
            'low': 0.7,
            'nice_to_have': 0.5
        }
        return weights.get(priority.lower(), 1.0)


class ProjectDomainService:
    """
    Domain service for project-related business logic.
    Handles operations that span multiple project entities.
    """

    def analyze_domain_model(
        self,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze requirements to extract domain model insights."""
        bounded_contexts = self._extract_bounded_contexts(requirements)
        domain_entities = self._extract_domain_entities(requirements)
        aggregate_roots = self._identify_aggregate_roots(requirements, domain_entities)

        return {
            'bounded_contexts': bounded_contexts,
            'domain_entities': domain_entities,
            'aggregate_roots': aggregate_roots,
            'context_map': self._build_context_map(bounded_contexts, requirements),
            'ubiquitous_language': self._extract_ubiquitous_language(requirements)
        }

    def _extract_bounded_contexts(
        self,
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract bounded contexts from requirements."""
        contexts = {}

        for req in requirements:
            context_name = req.get('bounded_context')
            if context_name:
                if context_name not in contexts:
                    contexts[context_name] = {
                        'name': context_name,
                        'requirements': [],
                        'entities': set(),
                        'aggregates': set()
                    }

                contexts[context_name]['requirements'].append(req.get('id'))

                if req.get('domain_entity'):
                    contexts[context_name]['entities'].add(req.get('domain_entity'))

                if req.get('aggregate_root'):
                    contexts[context_name]['aggregates'].add(req.get('aggregate_root'))

        # Convert sets to lists for JSON serialization
        for context in contexts.values():
            context['entities'] = list(context['entities'])
            context['aggregates'] = list(context['aggregates'])

        return list(contexts.values())

    def _extract_domain_entities(
        self,
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract domain entities from requirements."""
        entities = {}

        for req in requirements:
            entity_name = req.get('domain_entity')
            if entity_name:
                if entity_name not in entities:
                    entities[entity_name] = {
                        'name': entity_name,
                        'bounded_context': req.get('bounded_context'),
                        'requirements': [],
                        'attributes': set(),
                        'business_rules': set()
                    }

                entities[entity_name]['requirements'].append(req.get('id'))

                # Extract potential attributes from requirement description
                description = req.get('description', '').lower()
                potential_attributes = self._extract_attributes_from_text(description)
                entities[entity_name]['attributes'].update(potential_attributes)

        # Convert sets to lists for JSON serialization
        for entity in entities.values():
            entity['attributes'] = list(entity['attributes'])
            entity['business_rules'] = list(entity['business_rules'])

        return list(entities.values())

    def _identify_aggregate_roots(
        self,
        requirements: List[Dict[str, Any]],
        domain_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify potential aggregate roots."""
        aggregates = {}

        for req in requirements:
            aggregate_name = req.get('aggregate_root')
            if aggregate_name:
                if aggregate_name not in aggregates:
                    aggregates[aggregate_name] = {
                        'name': aggregate_name,
                        'bounded_context': req.get('bounded_context'),
                        'root_entity': req.get('domain_entity'),
                        'requirements': [],
                        'child_entities': set(),
                        'domain_events': set()
                    }

                aggregates[aggregate_name]['requirements'].append(req.get('id'))

        # Convert sets to lists for JSON serialization
        for aggregate in aggregates.values():
            aggregate['child_entities'] = list(aggregate['child_entities'])
            aggregate['domain_events'] = list(aggregate['domain_events'])

        return list(aggregates.values())

    def _build_context_map(
        self,
        bounded_contexts: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Build a context map showing relationships between bounded contexts."""
        context_map = {}

        for context in bounded_contexts:
            context_name = context['name']
            context_map[context_name] = []

            # Find related contexts based on requirement dependencies
            for req in requirements:
                if req.get('bounded_context') == context_name:
                    depends_on = req.get('depends_on', [])

                    for dep_id in depends_on:
                        # Find the bounded context of the dependency
                        for other_req in requirements:
                            if other_req.get('id') == dep_id:
                                other_context = other_req.get('bounded_context')
                                if other_context and other_context != context_name:
                                    if other_context not in context_map[context_name]:
                                        context_map[context_name].append(other_context)

        return context_map

    def _extract_ubiquitous_language(
        self,
        requirements: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract terms for the ubiquitous language."""
        terms = set()

        for req in requirements:
            # Extract domain-specific terms from titles and descriptions
            title = req.get('title', '').lower()
            description = req.get('description', '').lower()

            # Simple extraction - can be made more sophisticated with NLP
            domain_terms = self._extract_domain_terms(title + ' ' + description)
            terms.update(domain_terms)

        return sorted(list(terms))

    def _extract_attributes_from_text(self, text: str) -> Set[str]:
        """Extract potential entity attributes from text."""
        # Simple pattern matching - can be enhanced with NLP
        attribute_keywords = [
            'name', 'title', 'description', 'status', 'type', 'date',
            'time', 'amount', 'quantity', 'price', 'value', 'id',
            'identifier', 'code', 'reference', 'number'
        ]

        attributes = set()
        words = text.split()

        for word in words:
            if word.lower() in attribute_keywords:
                attributes.add(word.lower())

        return attributes

    def _extract_domain_terms(self, text: str) -> Set[str]:
        """Extract domain-specific terms from text."""
        # Simple extraction - in practice, this would use NLP techniques
        business_terms = set()
        words = text.split()

        # Common business domain terms
        domain_keywords = [
            'user', 'customer', 'order', 'product', 'account', 'payment',
            'invoice', 'subscription', 'profile', 'preferences', 'settings',
            'notification', 'report', 'dashboard', 'analytics', 'metric'
        ]

        for word in words:
            clean_word = word.lower().strip('.,!?()[]{}":;')
            if clean_word in domain_keywords and len(clean_word) > 2:
                business_terms.add(clean_word)

        return business_terms
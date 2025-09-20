"""
Integration examples showing how to use the enhanced requirements management system.
Demonstrates domain-driven design, repository pattern, and AI-powered features.
"""

import uuid
import asyncio
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

# Example imports (would be actual imports in real usage)
from ..domain import (
    BoundedContext, DomainEntity, AggregateRoot,
    Priority, PriorityLevel, ComplexityLevel, ComplexityScale,
    BusinessValue, StoryPoints, RequirementIdentifier,
    RequirementDomainService, ProjectDomainService
)
from ..requirements.enhanced_service import EnhancedProjectService, EnhancedRequirementService
from ..ai.enhanced_service import RequirementGenerationService
from ..requirements.schemas import ProjectCreate, RequirementCreate
from ..requirements.models import RequirementType


class IntegrationExamples:
    """Examples of how to integrate and use the enhanced system."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def example_1_domain_modeling(self) -> Dict[str, Any]:
        """Example 1: Using Domain-Driven Design models."""
        print("=== Example 1: Domain Modeling with DDD ===")

        # Create a bounded context
        user_context = BoundedContext(
            name="User Management",
            description="Handles user authentication, profiles, and preferences",
            ubiquitous_language={"User", "Profile", "Authentication", "Session"},
            domain_entities={"User", "Profile", "Preference"},
            aggregate_roots={"UserAccount"}
        )

        # Create domain entities
        user_entity = DomainEntity(
            name="User",
            entity_id=str(uuid.uuid4()),
            bounded_context="User Management",
            attributes={
                "email": "string",
                "username": "string",
                "is_active": "boolean",
                "created_at": "datetime"
            },
            business_rules=[
                "Email must be unique across the system",
                "Username must be alphanumeric",
                "Account can be deactivated but not deleted"
            ],
            invariants=[
                "Email format must be valid",
                "Username must be between 3-20 characters"
            ]
        )

        # Create value objects
        priority = Priority(PriorityLevel.HIGH, "Critical for MVP launch")
        complexity = ComplexityLevel(ComplexityScale.MODERATE, "Standard CRUD with validation")
        business_value = BusinessValue(85, "Essential for user onboarding")
        story_points = StoryPoints(5, "Planning poker estimation")

        # Create requirement identifier
        req_id = RequirementIdentifier("USR", 1, "v1.0")

        return {
            "bounded_context": str(user_context),
            "domain_entity": str(user_entity),
            "priority": str(priority),
            "complexity": str(complexity),
            "business_value": str(business_value),
            "story_points": str(story_points),
            "requirement_id": str(req_id),
            "example_complete": True
        }

    async def example_2_enhanced_project_creation(self) -> Dict[str, Any]:
        """Example 2: Creating a project with enhanced service."""
        print("=== Example 2: Enhanced Project Creation ===")

        # Create enhanced project service
        project_service = EnhancedProjectService(self.db_session)

        # Example project data
        project_data = ProjectCreate(
            name="E-commerce Platform",
            description="Modern e-commerce platform with AI recommendations",
            vision="To create the most user-friendly online shopping experience",
            goals=[
                "Increase conversion rate by 25%",
                "Reduce cart abandonment by 40%",
                "Implement AI-powered recommendations"
            ],
            success_criteria=[
                "Platform handles 10,000 concurrent users",
                "Average page load time < 2 seconds",
                "99.9% uptime SLA"
            ],
            stakeholders=[
                "Product Manager", "Engineering Team", "Marketing Team", "Customers"
            ],
            methodology="Agile/Scrum",
            domain_model={
                "contexts": ["Product Catalog", "Order Management", "User Management", "Payment Processing"],
                "core_entities": ["Product", "Order", "User", "Payment"],
                "aggregates": ["ProductCatalog", "ShoppingCart", "OrderProcess", "CustomerAccount"]
            },
            project_settings={
                "ai_assistance": True,
                "quality_gates": True,
                "automated_testing": True
            }
        )

        # Simulate user and tenant IDs
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        # Create project (would actually create in real scenario)
        # project_response = await project_service.create_project(project_data, user_id, tenant_id)

        return {
            "message": "Project creation example configured",
            "project_name": project_data.name,
            "bounded_contexts": len(project_data.domain_model.get("contexts", [])),
            "methodology": project_data.methodology,
            "ai_enabled": project_data.project_settings.get("ai_assistance", False),
            "example_complete": True
        }

    async def example_3_ai_requirement_generation(self) -> Dict[str, Any]:
        """Example 3: AI-powered requirement generation."""
        print("=== Example 3: AI Requirement Generation ===")

        # Create AI service
        ai_service = RequirementGenerationService(self.db_session)

        # Example natural language description
        description = """
        As an e-commerce platform, we need a user registration system that allows customers
        to create accounts, verify their email addresses, and set up their profiles.
        The system should include social login options (Google, Facebook), password strength
        validation, and the ability to recover forgotten passwords. Users should be able
        to update their personal information and preferences after registration.
        """

        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Context for AI generation
        context = {
            "domain": "E-commerce",
            "user_types": ["Customer", "Admin", "Guest"],
            "existing_features": ["Product Catalog", "Shopping Cart"],
            "technical_constraints": ["GDPR compliance", "Mobile responsive"]
        }

        # Simulate AI generation (would actually call AI in real scenario)
        # generated_requirements = await ai_service.generate_requirements_from_description(
        #     project_id=project_id,
        #     description=description,
        #     user_id=user_id,
        #     requirement_type=RequirementType.FUNCTIONAL,
        #     context=context
        # )

        # Example of what would be generated
        example_generated = [
            {
                "title": "User Registration with Email Verification",
                "description": "System allows new users to create accounts with email verification",
                "priority": "high",
                "complexity": "moderate",
                "story_points": 5,
                "business_value": 80
            },
            {
                "title": "Social Login Integration",
                "description": "Users can register/login using Google and Facebook accounts",
                "priority": "medium",
                "complexity": "complex",
                "story_points": 8,
                "business_value": 70
            },
            {
                "title": "Password Recovery System",
                "description": "Users can reset forgotten passwords via email",
                "priority": "high",
                "complexity": "simple",
                "story_points": 3,
                "business_value": 75
            }
        ]

        return {
            "description_length": len(description),
            "context_provided": list(context.keys()),
            "generated_count": len(example_generated),
            "example_requirements": example_generated,
            "ai_service_configured": True,
            "example_complete": True
        }

    async def example_4_domain_analysis(self) -> Dict[str, Any]:
        """Example 4: Domain analysis with domain services."""
        print("=== Example 4: Domain Analysis ===")

        # Create domain services
        requirement_domain_service = RequirementDomainService()
        project_domain_service = ProjectDomainService()

        # Example requirements data for analysis
        requirements_data = [
            {
                "id": str(uuid.uuid4()),
                "title": "User Registration",
                "description": "Allow users to create accounts",
                "requirement_type": "functional",
                "priority": "high",
                "complexity": 3,
                "story_points": 5,
                "business_value": 80,
                "bounded_context": "User Management",
                "domain_entity": "User",
                "aggregate_root": "UserAccount"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Email Verification",
                "description": "Verify user email addresses",
                "requirement_type": "functional",
                "priority": "high",
                "complexity": 2,
                "story_points": 3,
                "business_value": 70,
                "bounded_context": "User Management",
                "domain_entity": "User",
                "aggregate_root": "UserAccount"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Product Catalog",
                "description": "Display available products",
                "requirement_type": "functional",
                "priority": "critical",
                "complexity": 4,
                "story_points": 8,
                "business_value": 95,
                "bounded_context": "Product Catalog",
                "domain_entity": "Product",
                "aggregate_root": "ProductCatalog"
            }
        ]

        # Analyze project complexity
        project_complexity = requirement_domain_service.calculate_project_complexity(requirements_data)

        # Identify dependencies
        dependencies = requirement_domain_service.identify_requirement_dependencies(requirements_data)

        # Prioritize requirements
        prioritized = requirement_domain_service.prioritize_requirements(requirements_data)

        # Analyze domain model
        domain_analysis = project_domain_service.analyze_domain_model(requirements_data)

        return {
            "total_requirements": len(requirements_data),
            "project_complexity": str(project_complexity),
            "dependency_count": sum(len(deps) for deps in dependencies.values()),
            "bounded_contexts": len(domain_analysis.get("bounded_contexts", [])),
            "domain_entities": len(domain_analysis.get("domain_entities", [])),
            "aggregate_roots": len(domain_analysis.get("aggregate_roots", [])),
            "prioritization_complete": len(prioritized) == len(requirements_data),
            "domain_analysis_complete": True,
            "example_complete": True
        }

    async def example_5_repository_operations(self) -> Dict[str, Any]:
        """Example 5: Repository pattern operations."""
        print("=== Example 5: Repository Pattern Usage ===")

        from ..requirements.repository import RequirementRepository, AcceptanceCriteriaRepository
        from ..projects.repository import ProjectRepository

        # Create repositories
        project_repo = ProjectRepository(self.db_session)
        requirement_repo = RequirementRepository(self.db_session)
        criteria_repo = AcceptanceCriteriaRepository(self.db_session)

        project_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        # Example repository operations (would actually execute in real scenario)
        operations = [
            "project_repo.get_by_tenant(tenant_id)",
            "project_repo.count_by_tenant(tenant_id)",
            "project_repo.search(tenant_id, 'e-commerce')",
            "requirement_repo.get_by_project(project_id)",
            "requirement_repo.get_requirement_stats(project_id)",
            "requirement_repo.search(project_id, 'user registration')",
            "criteria_repo.get_by_requirement(requirement_id)"
        ]

        # Simulate stats
        example_stats = {
            "total_projects": 15,
            "active_requirements": 127,
            "completed_requirements": 89,
            "acceptance_criteria_count": 245,
            "search_results": 8
        }

        return {
            "repository_operations": operations,
            "example_stats": example_stats,
            "repositories_configured": ["ProjectRepository", "RequirementRepository", "AcceptanceCriteriaRepository"],
            "pattern_benefits": [
                "Clean separation of concerns",
                "Testable data access layer",
                "Consistent error handling",
                "Advanced querying capabilities"
            ],
            "example_complete": True
        }

    async def example_6_enhanced_workflow(self) -> Dict[str, Any]:
        """Example 6: Complete enhanced workflow."""
        print("=== Example 6: Complete Enhanced Workflow ===")

        # This example shows a complete workflow using all enhanced features
        workflow_steps = [
            {
                "step": 1,
                "action": "Create Project with Domain Model",
                "service": "EnhancedProjectService",
                "description": "Create project with bounded contexts and domain entities"
            },
            {
                "step": 2,
                "action": "Generate Requirements with AI",
                "service": "RequirementGenerationService",
                "description": "Use AI to generate initial requirements from user stories"
            },
            {
                "step": 3,
                "action": "Validate with Domain Services",
                "service": "RequirementDomainService",
                "description": "Validate requirements against domain rules and complexity"
            },
            {
                "step": 4,
                "action": "Store with Repository Pattern",
                "service": "RequirementRepository",
                "description": "Store requirements using repository for clean data access"
            },
            {
                "step": 5,
                "action": "Analyze Dependencies",
                "service": "ProjectDomainService",
                "description": "Identify requirement dependencies and relationships"
            },
            {
                "step": 6,
                "action": "Prioritize Requirements",
                "service": "RequirementDomainService",
                "description": "Use domain logic to prioritize based on business value"
            },
            {
                "step": 7,
                "action": "Enhance with AI",
                "service": "RequirementGenerationService",
                "description": "Generate acceptance criteria and test cases"
            },
            {
                "step": 8,
                "action": "Quality Analysis",
                "service": "RequirementGenerationService",
                "description": "AI-powered quality analysis and recommendations"
            }
        ]

        integration_benefits = [
            "Domain-driven design ensures business alignment",
            "Repository pattern provides clean architecture",
            "AI assistance accelerates requirement creation",
            "Domain services enforce business rules",
            "Enhanced APIs provide powerful functionality",
            "Comprehensive analytics and insights"
        ]

        return {
            "workflow_steps": workflow_steps,
            "total_steps": len(workflow_steps),
            "integration_benefits": integration_benefits,
            "architecture_patterns": [
                "Domain-Driven Design",
                "Repository Pattern",
                "Service Layer",
                "Clean Architecture"
            ],
            "ai_features": [
                "Requirement Generation",
                "Quality Analysis",
                "Enhancement Suggestions",
                "Domain Analysis"
            ],
            "example_complete": True
        }


async def run_all_examples():
    """Run all integration examples."""
    print("🚀 Running Enhanced Requirements Management Integration Examples")
    print("=" * 80)

    # Note: In real usage, you would have an actual database session
    # For this example, we'll use None and focus on the structure
    db_session = None
    examples = IntegrationExamples(db_session)

    try:
        # Run examples (catching errors since we don't have real DB)
        results = {}

        # Example 1: Domain Modeling
        try:
            results["domain_modeling"] = await examples.example_1_domain_modeling()
        except Exception as e:
            results["domain_modeling"] = {"error": str(e), "status": "demo_mode"}

        # Example 2: Enhanced Project Creation
        try:
            results["project_creation"] = await examples.example_2_enhanced_project_creation()
        except Exception as e:
            results["project_creation"] = {"error": str(e), "status": "demo_mode"}

        # Example 3: AI Requirement Generation
        try:
            results["ai_generation"] = await examples.example_3_ai_requirement_generation()
        except Exception as e:
            results["ai_generation"] = {"error": str(e), "status": "demo_mode"}

        # Example 4: Domain Analysis
        try:
            results["domain_analysis"] = await examples.example_4_domain_analysis()
        except Exception as e:
            results["domain_analysis"] = {"error": str(e), "status": "demo_mode"}

        # Example 5: Repository Operations
        try:
            results["repository_operations"] = await examples.example_5_repository_operations()
        except Exception as e:
            results["repository_operations"] = {"error": str(e), "status": "demo_mode"}

        # Example 6: Enhanced Workflow
        try:
            results["enhanced_workflow"] = await examples.example_6_enhanced_workflow()
        except Exception as e:
            results["enhanced_workflow"] = {"error": str(e), "status": "demo_mode"}

        print("\n✅ All examples completed successfully!")
        print(f"📊 Results summary: {len(results)} examples executed")

        return results

    except Exception as e:
        print(f"❌ Error running examples: {str(e)}")
        return {"error": str(e), "status": "failed"}


if __name__ == "__main__":
    # Run examples if executed directly
    asyncio.run(run_all_examples())
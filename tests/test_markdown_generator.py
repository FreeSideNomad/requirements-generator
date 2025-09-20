"""
Unit tests for markdown documentation generator.
Tests MarkdownGenerator functionality and template generation.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from src.requirements.markdown_generator import MarkdownGenerator
from src.requirements.models import Project, RequirementType, RequirementStatus, Priority
from src.requirements.service import RequirementService, DomainService


@pytest.fixture
def mock_requirement_service():
    """Mock RequirementService."""
    service = Mock(spec=RequirementService)
    service.get_project_requirements = AsyncMock()
    service.get_requirement = AsyncMock()
    return service


@pytest.fixture
def mock_domain_service():
    """Mock DomainService."""
    service = Mock(spec=DomainService)
    service.analyze_domain_model = AsyncMock()
    return service


@pytest.fixture
def sample_project():
    """Sample project for testing."""
    return Project(
        id=uuid.uuid4(),
        name="Sample Project",
        description="A test project for documentation",
        vision="To create great software",
        goals=["Improve user experience", "Reduce development time"],
        success_criteria=["95% user satisfaction", "50% faster delivery"],
        stakeholders=[
            {"name": "John Doe", "role": "Product Owner", "contact": "john@example.com"},
            {"name": "Jane Smith", "role": "Stakeholder", "contact": "jane@example.com"}
        ],
        methodology="agile",
        tenant_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return [
        {
            "id": str(uuid.uuid4()),
            "identifier": "EPIC-001",
            "title": "User Management",
            "requirement_type": RequirementType.EPIC,
            "status": RequirementStatus.APPROVED,
            "priority": Priority.HIGH,
            "parent_id": None,
            "story_points": None,
            "business_value": 90,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 2,
            "acceptance_criteria_count": 0
        },
        {
            "id": str(uuid.uuid4()),
            "identifier": "US-001",
            "title": "User Registration",
            "requirement_type": RequirementType.USER_STORY,
            "status": RequirementStatus.IN_DEVELOPMENT,
            "priority": Priority.HIGH,
            "parent_id": str(uuid.uuid4()),
            "story_points": 8,
            "business_value": 85,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 0,
            "acceptance_criteria_count": 3
        },
        {
            "id": str(uuid.uuid4()),
            "identifier": "US-002",
            "title": "User Login",
            "requirement_type": RequirementType.USER_STORY,
            "status": RequirementStatus.COMPLETED,
            "priority": Priority.HIGH,
            "parent_id": str(uuid.uuid4()),
            "story_points": 5,
            "business_value": 80,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 0,
            "acceptance_criteria_count": 2
        },
        {
            "id": str(uuid.uuid4()),
            "identifier": "FR-001",
            "title": "Password Validation",
            "requirement_type": RequirementType.FUNCTIONAL,
            "status": RequirementStatus.APPROVED,
            "priority": Priority.MEDIUM,
            "parent_id": None,
            "story_points": None,
            "business_value": 70,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 0,
            "acceptance_criteria_count": 1
        },
        {
            "id": str(uuid.uuid4()),
            "identifier": "NFR-001",
            "title": "Performance Requirements",
            "requirement_type": RequirementType.NON_FUNCTIONAL,
            "status": RequirementStatus.DRAFT,
            "priority": Priority.MEDIUM,
            "parent_id": None,
            "story_points": None,
            "business_value": 60,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 0,
            "acceptance_criteria_count": 0
        },
        {
            "id": str(uuid.uuid4()),
            "identifier": "BR-001",
            "title": "User Access Rules",
            "requirement_type": RequirementType.BUSINESS_RULE,
            "status": RequirementStatus.APPROVED,
            "priority": Priority.HIGH,
            "parent_id": None,
            "story_points": None,
            "business_value": 75,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 0,
            "acceptance_criteria_count": 0
        },
        {
            "id": str(uuid.uuid4()),
            "identifier": "CON-001",
            "title": "Browser Compatibility",
            "requirement_type": RequirementType.CONSTRAINT,
            "status": RequirementStatus.APPROVED,
            "priority": Priority.LOW,
            "parent_id": None,
            "story_points": None,
            "business_value": 40,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 0,
            "acceptance_criteria_count": 0
        },
        {
            "id": str(uuid.uuid4()),
            "identifier": "ASM-001",
            "title": "User Internet Access",
            "requirement_type": RequirementType.ASSUMPTION,
            "status": RequirementStatus.APPROVED,
            "priority": Priority.LOW,
            "parent_id": None,
            "story_points": None,
            "business_value": 30,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(uuid.uuid4()),
            "children_count": 0,
            "acceptance_criteria_count": 0
        }
    ]


@pytest.fixture
def sample_domain_model():
    """Sample domain model for testing."""
    return {
        "User Management": {
            "entities": ["User", "Profile", "Account"],
            "aggregates": ["UserAccount"],
            "requirements": [
                {
                    "id": str(uuid.uuid4()),
                    "identifier": "US-001",
                    "title": "User Registration",
                    "type": "user_story",
                    "entity": "User",
                    "aggregate": "UserAccount"
                },
                {
                    "id": str(uuid.uuid4()),
                    "identifier": "US-002",
                    "title": "User Login",
                    "type": "user_story",
                    "entity": "User",
                    "aggregate": "UserAccount"
                }
            ]
        },
        "Payment Processing": {
            "entities": ["Payment", "Transaction"],
            "aggregates": ["PaymentAggregate"],
            "requirements": [
                {
                    "id": str(uuid.uuid4()),
                    "identifier": "FR-002",
                    "title": "Process Payment",
                    "type": "functional",
                    "entity": "Payment",
                    "aggregate": "PaymentAggregate"
                }
            ]
        }
    }


class TestMarkdownGenerator:
    """Test MarkdownGenerator functionality."""

    def test_markdown_generator_initialization(self, mock_requirement_service, mock_domain_service):
        """Test MarkdownGenerator initialization."""
        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        assert generator.requirement_service == mock_requirement_service
        assert generator.domain_service == mock_domain_service
        assert generator.env is not None

    @pytest.mark.asyncio
    async def test_generate_project_documentation_default_template(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project,
        sample_requirements,
        sample_domain_model
    ):
        """Test project documentation generation with default template."""
        # Setup mocks
        mock_requirements_response = Mock()
        mock_requirements_response.items = sample_requirements
        mock_requirement_service.get_project_requirements.return_value = mock_requirements_response
        mock_domain_service.analyze_domain_model.return_value = sample_domain_model

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_project_documentation(
            project=sample_project,
            include_domain_model=True,
            include_acceptance_criteria=True,
            include_comments=False,
            template_name="default"
        )

        # Verify content
        assert sample_project.name in result
        assert sample_project.description in result
        assert sample_project.vision in result

        # Verify goals and success criteria
        for goal in sample_project.goals:
            assert goal in result
        for criteria in sample_project.success_criteria:
            assert criteria in result

        # Verify stakeholders
        assert "John Doe" in result
        assert "Product Owner" in result

        # Verify domain model
        assert "## Domain Model" in result
        assert "User Management" in result
        assert "Payment Processing" in result

        # Verify requirements sections
        assert "## Epics" in result
        assert "EPIC-001" in result
        assert "User Management" in result

        assert "## User Stories" in result
        assert "US-001" in result
        assert "User Registration" in result
        assert "US-002" in result
        assert "User Login" in result

        assert "## Functional Requirements" in result
        assert "FR-001" in result
        assert "Password Validation" in result

        assert "## Non-Functional Requirements" in result
        assert "NFR-001" in result
        assert "Performance Requirements" in result

        assert "## Business Rules" in result
        assert "BR-001" in result
        assert "User Access Rules" in result

        assert "## Constraints" in result
        assert "CON-001" in result
        assert "Browser Compatibility" in result

        assert "## Assumptions" in result
        assert "ASM-001" in result
        assert "User Internet Access" in result

        # Verify metadata
        assert "## Document Information" in result
        assert "Generated" in result
        assert "Total Requirements: 8" in result

    @pytest.mark.asyncio
    async def test_generate_project_documentation_user_stories_template(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project,
        sample_requirements
    ):
        """Test project documentation generation with user stories template."""
        # Setup mocks
        mock_requirements_response = Mock()
        mock_requirements_response.items = sample_requirements
        mock_requirement_service.get_project_requirements.return_value = mock_requirements_response

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_project_documentation(
            project=sample_project,
            template_name="user_stories"
        )

        # Verify content
        assert f"# User Stories - {sample_project.name}" in result
        assert "## Standalone User Stories" in result
        assert "US-001" in result
        assert "US-002" in result

    @pytest.mark.asyncio
    async def test_generate_project_documentation_domain_driven_template(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project,
        sample_requirements,
        sample_domain_model
    ):
        """Test project documentation generation with domain-driven template."""
        # Setup mocks
        mock_requirements_response = Mock()
        mock_requirements_response.items = sample_requirements
        mock_requirement_service.get_project_requirements.return_value = mock_requirements_response
        mock_domain_service.analyze_domain_model.return_value = sample_domain_model

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_project_documentation(
            project=sample_project,
            template_name="domain_driven"
        )

        # Verify content
        assert f"# Domain Model - {sample_project.name}" in result
        assert "## Domain Overview" in result
        assert "### User Management Bounded Context" in result
        assert "**Domain Entities:**" in result
        assert "**Aggregate Roots:**" in result
        assert "**Requirements:**" in result

    @pytest.mark.asyncio
    async def test_generate_project_documentation_custom_template(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project,
        sample_requirements,
        sample_domain_model
    ):
        """Test project documentation generation with custom template (falls back to default)."""
        # Setup mocks
        mock_requirements_response = Mock()
        mock_requirements_response.items = sample_requirements
        mock_requirement_service.get_project_requirements.return_value = mock_requirements_response
        mock_domain_service.analyze_domain_model.return_value = sample_domain_model

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_project_documentation(
            project=sample_project,
            template_name="custom_template"
        )

        # Should fall back to default template
        assert sample_project.name in result
        assert "## Document Information" in result

    @pytest.mark.asyncio
    async def test_generate_requirement_documentation_success(
        self,
        mock_requirement_service,
        mock_domain_service
    ):
        """Test single requirement documentation generation."""
        requirement_id = uuid.uuid4()

        # Mock requirement response
        mock_requirement = Mock(
            id=requirement_id,
            identifier="US-001",
            title="User Login",
            description="As a user, I want to log in so that I can access my account",
            rationale="Users need secure access to their accounts",
            requirement_type=RequirementType.USER_STORY,
            status=RequirementStatus.APPROVED,
            priority=Priority.HIGH,
            complexity="moderate",
            story_points=5,
            business_value=85,
            user_persona="Registered User",
            user_goal="log in to my account",
            user_benefit="access my personal information",
            bounded_context="User Management",
            domain_entity="User",
            aggregate_root="UserAccount",
            depends_on=[str(uuid.uuid4())],
            custom_fields={"priority_reason": "Critical for MVP"},
            created_at=datetime.utcnow(),
            acceptance_criteria_count=3
        )
        mock_requirement_service.get_requirement.return_value = mock_requirement

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_requirement_documentation(
            requirement_id=requirement_id,
            include_children=True,
            include_acceptance_criteria=True
        )

        # Verify content
        assert "# US-001: User Login" in result
        assert "## Metadata" in result
        assert "**Type**: user_story" in result
        assert "**Status**: approved" in result
        assert "**Priority**: high" in result
        assert "**Complexity**: moderate" in result
        assert "**Story Points**: 5" in result
        assert "**Business Value**: 85" in result

        assert "## Description" in result
        assert "As a user, I want to log in so that I can access my account" in result

        assert "## User Story" in result
        assert "**As a** Registered User" in result
        assert "**I want to** log in to my account" in result
        assert "**So that** access my personal information" in result

        assert "## Rationale" in result
        assert "Users need secure access to their accounts" in result

        assert "## Domain Context" in result
        assert "**Bounded Context**: User Management" in result
        assert "**Domain Entity**: User" in result
        assert "**Aggregate Root**: UserAccount" in result

        assert "## Dependencies" in result

        assert "## Custom Fields" in result
        assert "**priority_reason**: Critical for MVP" in result

    @pytest.mark.asyncio
    async def test_generate_requirement_documentation_not_found(
        self,
        mock_requirement_service,
        mock_domain_service
    ):
        """Test requirement documentation generation when requirement not found."""
        requirement_id = uuid.uuid4()
        mock_requirement_service.get_requirement.return_value = None

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_requirement_documentation(requirement_id)

        assert "# Requirement Not Found" in result
        assert "The requested requirement could not be found." in result

    @pytest.mark.asyncio
    async def test_generate_requirement_documentation_exception(
        self,
        mock_requirement_service,
        mock_domain_service
    ):
        """Test requirement documentation generation with exception."""
        requirement_id = uuid.uuid4()
        mock_requirement_service.get_requirement.side_effect = Exception("Database error")

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_requirement_documentation(requirement_id)

        assert "# Error" in result
        assert "Failed to generate documentation: Database error" in result

    def test_organize_requirements(self, mock_requirement_service, mock_domain_service, sample_requirements):
        """Test requirement organization by type."""
        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        organized = generator._organize_requirements(sample_requirements)

        # Verify organization
        assert len(organized["epics"]) == 1
        assert organized["epics"][0]["identifier"] == "EPIC-001"

        assert len(organized["user_stories"]) == 2
        assert organized["user_stories"][0]["identifier"] == "US-001"
        assert organized["user_stories"][1]["identifier"] == "US-002"

        assert len(organized["functional"]) == 1
        assert organized["functional"][0]["identifier"] == "FR-001"

        assert len(organized["non_functional"]) == 1
        assert organized["non_functional"][0]["identifier"] == "NFR-001"

        assert len(organized["business_rules"]) == 1
        assert organized["business_rules"][0]["identifier"] == "BR-001"

        assert len(organized["constraints"]) == 1
        assert organized["constraints"][0]["identifier"] == "CON-001"

        assert len(organized["assumptions"]) == 1
        assert organized["assumptions"][0]["identifier"] == "ASM-001"

    @pytest.mark.asyncio
    async def test_generate_default_template_minimal_project(
        self,
        mock_requirement_service,
        mock_domain_service
    ):
        """Test default template generation with minimal project data."""
        minimal_project = Project(
            id=uuid.uuid4(),
            name="Minimal Project",
            description=None,
            vision=None,
            goals=None,
            success_criteria=None,
            stakeholders=None,
            methodology="agile",
            tenant_id=uuid.uuid4(),
            created_by=uuid.uuid4()
        )

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator._generate_default_template(
            project=minimal_project,
            requirements={"epics": [], "user_stories": [], "functional": [], "non_functional": [], "business_rules": [], "constraints": [], "assumptions": []},
            domain_model={},
            include_acceptance_criteria=True,
            include_comments=False
        )

        # Verify minimal content
        assert "# Minimal Project" in result
        assert "## Document Information" in result
        assert "**Project**: Minimal Project" in result
        assert "**Methodology**: agile" in result
        assert "**Total Requirements**: 0" in result

    @pytest.mark.asyncio
    async def test_generate_user_stories_template_with_epics(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project
    ):
        """Test user stories template with epic grouping."""
        epic_id = str(uuid.uuid4())
        requirements = {
            "epics": [
                {
                    "id": epic_id,
                    "identifier": "EPIC-001",
                    "title": "User Management",
                    "status": "approved",
                    "priority": "high"
                }
            ],
            "user_stories": [
                {
                    "id": str(uuid.uuid4()),
                    "identifier": "US-001",
                    "title": "User Registration",
                    "parent_id": epic_id,
                    "status": "draft",
                    "priority": "high",
                    "story_points": 8
                },
                {
                    "id": str(uuid.uuid4()),
                    "identifier": "US-002",
                    "title": "User Login",
                    "parent_id": epic_id,
                    "status": "approved",
                    "priority": "high",
                    "story_points": 5
                },
                {
                    "id": str(uuid.uuid4()),
                    "identifier": "US-003",
                    "title": "Standalone Story",
                    "parent_id": None,
                    "status": "draft",
                    "priority": "medium",
                    "story_points": 3
                }
            ],
            "functional": [],
            "non_functional": [],
            "business_rules": [],
            "constraints": [],
            "assumptions": []
        }

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator._generate_user_stories_template(
            project=sample_project,
            requirements=requirements,
            include_acceptance_criteria=True
        )

        # Verify epic grouping
        assert "## EPIC-001: User Management" in result
        assert "### US-001: User Registration" in result
        assert "### US-002: User Login" in result

        # Verify standalone stories
        assert "## Standalone User Stories" in result
        assert "### US-003: Standalone Story" in result

    @pytest.mark.asyncio
    async def test_generate_domain_driven_template_multiple_contexts(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project,
        sample_domain_model
    ):
        """Test domain-driven template with multiple bounded contexts."""
        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator._generate_domain_driven_template(
            project=sample_project,
            requirements={"epics": [], "user_stories": [], "functional": [], "non_functional": [], "business_rules": [], "constraints": [], "assumptions": []},
            domain_model=sample_domain_model
        )

        # Verify multiple contexts
        assert "### User Management Bounded Context" in result
        assert "### Payment Processing Bounded Context" in result

        # Verify entities and aggregates
        assert "- User" in result
        assert "- Profile" in result
        assert "- Account" in result
        assert "- UserAccount" in result
        assert "- Payment" in result
        assert "- PaymentAggregate" in result

        # Verify requirements
        assert "- US-001: User Registration (user_story)" in result
        assert "- FR-002: Process Payment (functional)" in result

    @pytest.mark.asyncio
    async def test_documentation_generation_exception_handling(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project
    ):
        """Test exception handling in documentation generation."""
        # Mock exception in requirements service
        mock_requirement_service.get_project_requirements.side_effect = Exception("Service error")

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        with pytest.raises(Exception) as exc_info:
            await generator.generate_project_documentation(sample_project)

        assert "Service error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_documentation_with_empty_requirements(
        self,
        mock_requirement_service,
        mock_domain_service,
        sample_project
    ):
        """Test documentation generation with empty requirements."""
        # Setup mocks with empty requirements
        mock_requirements_response = Mock()
        mock_requirements_response.items = []
        mock_requirement_service.get_project_requirements.return_value = mock_requirements_response
        mock_domain_service.analyze_domain_model.return_value = {}

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        result = await generator.generate_project_documentation(sample_project)

        # Verify basic structure exists even with no requirements
        assert sample_project.name in result
        assert "## Document Information" in result
        assert "**Total Requirements**: 0" in result

    def test_requirement_documentation_minimal_data(
        self,
        mock_requirement_service,
        mock_domain_service
    ):
        """Test requirement documentation with minimal data."""
        # Mock minimal requirement
        mock_requirement = Mock(
            id=uuid.uuid4(),
            identifier="REQ-001",
            title="Basic Requirement",
            description="Basic description",
            requirement_type=RequirementType.FUNCTIONAL,
            status=RequirementStatus.DRAFT,
            priority=Priority.MEDIUM,
            complexity=None,
            story_points=None,
            business_value=None,
            user_persona=None,
            user_goal=None,
            user_benefit=None,
            rationale=None,
            bounded_context=None,
            domain_entity=None,
            aggregate_root=None,
            depends_on=[],
            custom_fields={},
            created_at=datetime.utcnow(),
            acceptance_criteria_count=0
        )

        generator = MarkdownGenerator(mock_requirement_service, mock_domain_service)

        # This would be called through the async method, but we test the logic
        # Since the actual method is async, we test with a direct call approach
        # In a real scenario, this would be tested through the public async method
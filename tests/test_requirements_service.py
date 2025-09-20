"""
Unit tests for requirements service layer.
Tests ProjectService, RequirementService, and DomainService business logic.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.requirements.service import ProjectService, RequirementService, DomainService
from src.requirements.schemas import (
    ProjectCreate, ProjectUpdate, RequirementCreate, RequirementUpdate,
    AcceptanceCriteriaCreate, RequirementFilter
)
from src.requirements.models import (
    Project, ProjectMember, Requirement, AcceptanceCriteria,
    RequirementType, RequirementStatus, Priority, ComplexityLevel
)
from src.shared.exceptions import AppException


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def sample_project():
    """Sample project for testing."""
    mock_project = Mock()
    mock_project.id = uuid.uuid4()
    mock_project.name = "Test Project"
    mock_project.description = "Test description"
    mock_project.tenant_id = uuid.uuid4()
    mock_project.created_by = uuid.uuid4()
    mock_project.is_active = True
    mock_project.methodology = "agile"
    mock_project.created_at = datetime.utcnow()
    mock_project.updated_at = datetime.utcnow()
    return mock_project


@pytest.fixture
def sample_requirement():
    """Sample requirement for testing."""
    mock_requirement = Mock()
    mock_requirement.id = uuid.uuid4()
    mock_requirement.project_id = uuid.uuid4()
    mock_requirement.identifier = "US-001"
    mock_requirement.title = "User Login"
    mock_requirement.description = "User can log in"
    mock_requirement.requirement_type = RequirementType.USER_STORY
    mock_requirement.status = RequirementStatus.DRAFT
    mock_requirement.priority = Priority.HIGH
    mock_requirement.created_by = uuid.uuid4()
    mock_requirement.version = 1
    mock_requirement.created_at = datetime.utcnow()
    mock_requirement.updated_at = datetime.utcnow()
    return mock_requirement


class TestProjectService:
    """Test ProjectService functionality."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_db_session):
        """Test successful project creation."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        project_data = ProjectCreate(
            name="Test Project",
            description="Test description",
            methodology="scrum"
        )

        service = ProjectService(mock_db_session)

        # Mock flush to set project.id
        async def mock_flush():
            # Simulate the project getting an ID after flush
            pass
        mock_db_session.flush.side_effect = mock_flush

        result = await service.create_project(project_data, user_id, tenant_id)

        # Verify database operations
        assert mock_db_session.add.call_count == 2  # Project + ProjectMember
        mock_db_session.flush.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # Verify result
        assert result.name == "Test Project"
        assert result.description == "Test description"
        assert result.methodology == "scrum"
        assert result.tenant_id == tenant_id
        assert result.created_by == user_id

    @pytest.mark.asyncio
    async def test_create_project_failure(self, mock_db_session):
        """Test project creation failure."""
        mock_db_session.commit.side_effect = Exception("Database error")

        service = ProjectService(mock_db_session)
        project_data = ProjectCreate(name="Test Project")

        with pytest.raises(AppException) as exc_info:
            await service.create_project(project_data, uuid.uuid4(), uuid.uuid4())

        assert exc_info.value.error_code == "PROJECT_CREATE_ERROR"
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_success(self, mock_db_session, sample_project):
        """Test successful project retrieval."""
        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_project
        mock_db_session.execute.return_value = mock_result

        service = ProjectService(mock_db_session)
        result = await service.get_project(sample_project.id)

        assert result == sample_project
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_db_session):
        """Test project not found."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = ProjectService(mock_db_session)
        result = await service.get_project(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_project_exception(self, mock_db_session):
        """Test project retrieval exception."""
        mock_db_session.execute.side_effect = Exception("Database error")

        service = ProjectService(mock_db_session)
        result = await service.get_project(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_projects_success(self, mock_db_session):
        """Test successful user projects retrieval."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        # Mock projects query result
        mock_project1 = Mock()
        mock_project1.id = uuid.uuid4()
        mock_project1.name = "Project 1"
        mock_project1.tenant_id = tenant_id
        mock_project1.created_by = user_id

        mock_project2 = Mock()
        mock_project2.id = uuid.uuid4()
        mock_project2.name = "Project 2"
        mock_project2.tenant_id = tenant_id
        mock_project2.created_by = user_id

        mock_projects = [mock_project1, mock_project2]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_projects

        # Mock count query result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2

        mock_db_session.execute.side_effect = [mock_result, mock_count_result]

        service = ProjectService(mock_db_session)
        projects, total = await service.get_user_projects(user_id, tenant_id, page=1, page_size=10)

        assert len(projects) == 2
        assert total == 2
        assert projects[0].name == "Project 1"
        assert projects[1].name == "Project 2"

    @pytest.mark.asyncio
    async def test_get_user_projects_exception(self, mock_db_session):
        """Test user projects retrieval exception."""
        mock_db_session.execute.side_effect = Exception("Database error")

        service = ProjectService(mock_db_session)
        projects, total = await service.get_user_projects(uuid.uuid4(), uuid.uuid4())

        assert projects == []
        assert total == 0


class TestRequirementService:
    """Test RequirementService functionality."""

    @pytest.mark.asyncio
    async def test_create_requirement_success(self, mock_db_session):
        """Test successful requirement creation."""
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        requirement_data = RequirementCreate(
            title="User Login",
            description="User can log in",
            requirement_type=RequirementType.USER_STORY,
            priority=Priority.HIGH,
            story_points=5
        )

        # Mock identifier generation
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_count_result

        service = RequirementService(mock_db_session)

        with patch.object(service, '_requirement_to_response') as mock_to_response:
            mock_response = Mock()
            mock_to_response.return_value = mock_response

            result = await service.create_requirement(project_id, requirement_data, user_id)

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_to_response.assert_called_once()

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_create_requirement_failure(self, mock_db_session):
        """Test requirement creation failure."""
        mock_db_session.execute.side_effect = Exception("Database error")

        service = RequirementService(mock_db_session)
        requirement_data = RequirementCreate(
            title="Test Requirement",
            description="Test description",
            requirement_type=RequirementType.FUNCTIONAL
        )

        with pytest.raises(AppException) as exc_info:
            await service.create_requirement(uuid.uuid4(), requirement_data, uuid.uuid4())

        assert exc_info.value.error_code == "REQUIREMENT_CREATE_ERROR"
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_identifier(self, mock_db_session):
        """Test requirement identifier generation."""
        project_id = uuid.uuid4()

        # Mock count query result
        mock_result = Mock()
        mock_result.scalar.return_value = 5  # 5 existing requirements
        mock_db_session.execute.return_value = mock_result

        service = RequirementService(mock_db_session)

        # Test different requirement types
        identifier = await service._generate_identifier(project_id, RequirementType.EPIC)
        assert identifier == "EPIC-006"

        identifier = await service._generate_identifier(project_id, RequirementType.USER_STORY)
        assert identifier == "US-006"

        identifier = await service._generate_identifier(project_id, RequirementType.FUNCTIONAL)
        assert identifier == "FR-006"

        identifier = await service._generate_identifier(project_id, RequirementType.NON_FUNCTIONAL)
        assert identifier == "NFR-006"

        identifier = await service._generate_identifier(project_id, RequirementType.BUSINESS_RULE)
        assert identifier == "BR-006"

        identifier = await service._generate_identifier(project_id, RequirementType.CONSTRAINT)
        assert identifier == "CON-006"

        identifier = await service._generate_identifier(project_id, RequirementType.ASSUMPTION)
        assert identifier == "ASM-006"

    @pytest.mark.asyncio
    async def test_get_requirement_success(self, mock_db_session, sample_requirement):
        """Test successful requirement retrieval."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_requirement
        mock_db_session.execute.return_value = mock_result

        service = RequirementService(mock_db_session)

        with patch.object(service, '_requirement_to_response') as mock_to_response:
            mock_response = Mock()
            mock_to_response.return_value = mock_response

            result = await service.get_requirement(sample_requirement.id)

        assert result == mock_response
        mock_to_response.assert_called_once_with(sample_requirement)

    @pytest.mark.asyncio
    async def test_get_requirement_not_found(self, mock_db_session):
        """Test requirement not found."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = RequirementService(mock_db_session)
        result = await service.get_requirement(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_update_requirement_success(self, mock_db_session, sample_requirement):
        """Test successful requirement update."""
        update_data = RequirementUpdate(
            title="Updated Title",
            status=RequirementStatus.APPROVED,
            story_points=8
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_requirement
        mock_db_session.execute.return_value = mock_result

        service = RequirementService(mock_db_session)

        with patch.object(service, '_requirement_to_response') as mock_to_response, \
             patch.object(service, '_should_create_version', return_value=False):
            mock_response = Mock()
            mock_to_response.return_value = mock_response

            result = await service.update_requirement(
                sample_requirement.id, update_data, uuid.uuid4()
            )

        assert result == mock_response
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_requirement_with_versioning(self, mock_db_session, sample_requirement):
        """Test requirement update with versioning."""
        update_data = RequirementUpdate(
            title="Major Change",
            change_reason="Stakeholder feedback"
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_requirement
        mock_db_session.execute.return_value = mock_result

        service = RequirementService(mock_db_session)

        with patch.object(service, '_requirement_to_response') as mock_to_response, \
             patch.object(service, '_should_create_version', return_value=True):
            mock_response = Mock()
            mock_to_response.return_value = mock_response

            result = await service.update_requirement(
                sample_requirement.id, update_data, uuid.uuid4()
            )

        # Verify versioning logic
        assert sample_requirement.version == 2  # Incremented from 1
        assert sample_requirement.change_reason == "Stakeholder feedback"

    @pytest.mark.asyncio
    async def test_should_create_version(self, mock_db_session, sample_requirement):
        """Test version creation logic."""
        service = RequirementService(mock_db_session)

        # Significant change (title)
        update_data = RequirementUpdate(title="New Title")
        should_version = service._should_create_version(sample_requirement, update_data)
        assert should_version is True

        # Significant change (description)
        update_data = RequirementUpdate(description="New Description")
        should_version = service._should_create_version(sample_requirement, update_data)
        assert should_version is True

        # Significant change (status)
        update_data = RequirementUpdate(status=RequirementStatus.APPROVED)
        should_version = service._should_create_version(sample_requirement, update_data)
        assert should_version is True

        # Non-significant change (story points)
        update_data = RequirementUpdate(story_points=8)
        should_version = service._should_create_version(sample_requirement, update_data)
        assert should_version is False

    @pytest.mark.asyncio
    async def test_delete_requirement_success(self, mock_db_session, sample_requirement):
        """Test successful requirement deletion."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_requirement
        mock_db_session.execute.return_value = mock_result

        service = RequirementService(mock_db_session)
        result = await service.delete_requirement(sample_requirement.id)

        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_requirement)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_requirement_not_found(self, mock_db_session):
        """Test requirement deletion when not found."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = RequirementService(mock_db_session)
        result = await service.delete_requirement(uuid.uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_get_project_requirements_with_filters(self, mock_db_session):
        """Test project requirements retrieval with filters."""
        project_id = uuid.uuid4()
        filters = RequirementFilter(
            requirement_type=RequirementType.USER_STORY,
            status=RequirementStatus.APPROVED,
            search_query="login"
        )

        # Mock requirements query result
        mock_requirements = [
            Mock(
                id=uuid.uuid4(),
                identifier="US-001",
                title="User Login",
                requirement_type=RequirementType.USER_STORY,
                status=RequirementStatus.APPROVED,
                priority=Priority.HIGH,
                children=[],
                acceptance_criteria=[]
            )
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_requirements

        # Mock count query result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        mock_db_session.execute.side_effect = [mock_count_result, mock_result]

        service = RequirementService(mock_db_session)
        result = await service.get_project_requirements(project_id, filters, page=1, page_size=20)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0]["identifier"] == "US-001"
        assert result.has_next is False
        assert result.has_previous is False

    @pytest.mark.asyncio
    async def test_create_acceptance_criteria_success(self, mock_db_session):
        """Test successful acceptance criteria creation."""
        requirement_id = uuid.uuid4()
        user_id = uuid.uuid4()

        criteria_data = AcceptanceCriteriaCreate(
            title="Login Success",
            description="User should be redirected",
            order_index=1
        )

        service = RequirementService(mock_db_session)
        result = await service.create_acceptance_criteria(requirement_id, criteria_data, user_id)

        assert result.title == "Login Success"
        assert result.requirement_id == requirement_id
        assert result.created_by == user_id
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_requirement_to_response(self, mock_db_session, sample_requirement):
        """Test requirement to response conversion."""
        # Mock relationship attributes
        sample_requirement.children = []
        sample_requirement.acceptance_criteria = [Mock(), Mock()]  # 2 criteria

        service = RequirementService(mock_db_session)
        result = await service._requirement_to_response(sample_requirement)

        assert result.id == sample_requirement.id
        assert result.identifier == sample_requirement.identifier
        assert result.title == sample_requirement.title
        assert result.children_count == 0
        assert result.acceptance_criteria_count == 2


class TestDomainService:
    """Test DomainService functionality."""

    @pytest.mark.asyncio
    async def test_get_bounded_contexts_success(self, mock_db_session):
        """Test successful bounded contexts retrieval."""
        project_id = uuid.uuid4()

        # Mock query result with bounded contexts
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("User Management",),
            ("Payment Processing",),
            ("User Management",),  # Duplicate
            ("Inventory",)
        ]
        mock_db_session.execute.return_value = mock_result

        service = DomainService(mock_db_session)
        result = await service.get_bounded_contexts(project_id)

        # Should be sorted and deduplicated
        assert result == ["Inventory", "Payment Processing", "User Management"]

    @pytest.mark.asyncio
    async def test_get_bounded_contexts_exception(self, mock_db_session):
        """Test bounded contexts retrieval exception."""
        mock_db_session.execute.side_effect = Exception("Database error")

        service = DomainService(mock_db_session)
        result = await service.get_bounded_contexts(uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_get_domain_entities_success(self, mock_db_session):
        """Test successful domain entities retrieval."""
        project_id = uuid.uuid4()

        # Mock query result with domain entities
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("User",),
            ("Account",),
            ("Payment",),
            ("User",)  # Duplicate
        ]
        mock_db_session.execute.return_value = mock_result

        service = DomainService(mock_db_session)
        result = await service.get_domain_entities(project_id)

        # Should be sorted and deduplicated
        assert result == ["Account", "Payment", "User"]

    @pytest.mark.asyncio
    async def test_get_domain_entities_with_context_filter(self, mock_db_session):
        """Test domain entities retrieval with bounded context filter."""
        project_id = uuid.uuid4()
        bounded_context = "User Management"

        mock_result = Mock()
        mock_result.fetchall.return_value = [("User",), ("Account",)]
        mock_db_session.execute.return_value = mock_result

        service = DomainService(mock_db_session)
        result = await service.get_domain_entities(project_id, bounded_context)

        assert result == ["Account", "User"]

    @pytest.mark.asyncio
    async def test_analyze_domain_model_success(self, mock_db_session):
        """Test successful domain model analysis."""
        project_id = uuid.uuid4()

        # Mock requirements with domain information
        mock_requirements = [
            Mock(
                id=uuid.uuid4(),
                identifier="US-001",
                title="User Login",
                requirement_type=RequirementType.USER_STORY,
                bounded_context="User Management",
                domain_entity="User",
                aggregate_root="UserAccount"
            ),
            Mock(
                id=uuid.uuid4(),
                identifier="US-002",
                title="User Profile",
                requirement_type=RequirementType.USER_STORY,
                bounded_context="User Management",
                domain_entity="Profile",
                aggregate_root="UserAccount"
            ),
            Mock(
                id=uuid.uuid4(),
                identifier="FR-001",
                title="Payment Processing",
                requirement_type=RequirementType.FUNCTIONAL,
                bounded_context="Payment",
                domain_entity="Payment",
                aggregate_root="PaymentAggregate"
            )
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_requirements
        mock_db_session.execute.return_value = mock_result

        service = DomainService(mock_db_session)
        result = await service.analyze_domain_model(project_id)

        # Verify structure
        assert "User Management" in result
        assert "Payment" in result

        user_context = result["User Management"]
        assert "User" in user_context["entities"]
        assert "Profile" in user_context["entities"]
        assert "UserAccount" in user_context["aggregates"]
        assert len(user_context["requirements"]) == 2

        payment_context = result["Payment"]
        assert "Payment" in payment_context["entities"]
        assert "PaymentAggregate" in payment_context["aggregates"]
        assert len(payment_context["requirements"]) == 1

    @pytest.mark.asyncio
    async def test_analyze_domain_model_exception(self, mock_db_session):
        """Test domain model analysis exception."""
        mock_db_session.execute.side_effect = Exception("Database error")

        service = DomainService(mock_db_session)
        result = await service.analyze_domain_model(uuid.uuid4())

        assert result == {}


class TestServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_project_service_database_connection_error(self, mock_db_session):
        """Test handling of database connection errors."""
        mock_db_session.execute.side_effect = Exception("Connection lost")

        service = ProjectService(mock_db_session)
        result = await service.get_project(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_requirement_service_invalid_data(self, mock_db_session):
        """Test requirement service with invalid data."""
        # This would be caught by Pydantic validation before reaching the service
        # but we test service robustness
        service = RequirementService(mock_db_session)

        with patch.object(service, '_generate_identifier', side_effect=Exception("Invalid data")):
            with pytest.raises(AppException):
                await service.create_requirement(
                    uuid.uuid4(),
                    RequirementCreate(
                        title="Test",
                        description="Test",
                        requirement_type=RequirementType.FUNCTIONAL
                    ),
                    uuid.uuid4()
                )

    @pytest.mark.asyncio
    async def test_pagination_edge_cases(self, mock_db_session):
        """Test pagination edge cases."""
        service = RequirementService(mock_db_session)

        # Mock empty results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0

        mock_db_session.execute.side_effect = [mock_count_result, mock_result]

        result = await service.get_project_requirements(
            uuid.uuid4(),
            page=1,
            page_size=20
        )

        assert result.total == 0
        assert len(result.items) == 0
        assert result.pages == 0
        assert result.has_next is False
        assert result.has_previous is False
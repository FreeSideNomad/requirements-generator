"""
Tests for enhanced repository layer.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.projects.repository import ProjectRepository, ProjectMemberRepository
from src.requirements.repository import RequirementRepository, AcceptanceCriteriaRepository
from src.projects.models import Project, ProjectMember
from src.requirements.models import Requirement, AcceptanceCriteria, RequirementType, Priority, RequirementStatus
from src.shared.exceptions import DatabaseError, NotFoundError


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    return Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project",
        tenant_id=uuid.uuid4(),
        created_by=uuid.uuid4()
    )


@pytest.fixture
def sample_requirement():
    """Create a sample requirement for testing."""
    return Requirement(
        id=uuid.uuid4(),
        identifier="REQ-0001",
        title="Test Requirement",
        description="A test requirement",
        requirement_type=RequirementType.FUNCTIONAL,
        priority=Priority.HIGH,
        status=RequirementStatus.DRAFT,
        project_id=uuid.uuid4(),
        created_by=uuid.uuid4()
    )


class TestProjectRepository:
    """Test ProjectRepository."""

    @pytest.mark.asyncio
    async def test_create_project(self, mock_db_session, sample_project):
        """Test creating a project."""
        repo = ProjectRepository(mock_db_session)

        # Mock flush and refresh
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await repo.create(sample_project)

        assert result == sample_project
        mock_db_session.add.assert_called_once_with(sample_project)
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_project)

    @pytest.mark.asyncio
    async def test_create_project_database_error(self, mock_db_session, sample_project):
        """Test handling database error during project creation."""
        repo = ProjectRepository(mock_db_session)

        # Mock database error
        mock_db_session.add.side_effect = Exception("Database connection failed")

        with pytest.raises(DatabaseError, match="Failed to create project"):
            await repo.create(sample_project)

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_db_session):
        """Test getting project by ID."""
        repo = ProjectRepository(mock_db_session)
        project_id = uuid.uuid4()

        # Mock database result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_project
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_by_id(project_id)

        assert result == sample_project
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db_session):
        """Test getting project by ID when not found."""
        repo = ProjectRepository(mock_db_session)
        project_id = uuid.uuid4()

        # Mock no result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_by_id(project_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_tenant(self, mock_db_session):
        """Test getting projects by tenant."""
        repo = ProjectRepository(mock_db_session)
        tenant_id = uuid.uuid4()

        # Mock database result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_project]
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_by_tenant(tenant_id, skip=0, limit=10)

        assert len(result) == 1
        assert result[0] == sample_project

    @pytest.mark.asyncio
    async def test_count_by_tenant(self, mock_db_session):
        """Test counting projects by tenant."""
        repo = ProjectRepository(mock_db_session)
        tenant_id = uuid.uuid4()

        # Mock count result
        mock_result = Mock()
        mock_result.scalar.return_value = 5
        mock_db_session.execute.return_value = mock_result

        result = await repo.count_by_tenant(tenant_id)

        assert result == 5

    @pytest.mark.asyncio
    async def test_search_projects(self, mock_db_session):
        """Test searching projects."""
        repo = ProjectRepository(mock_db_session)
        tenant_id = uuid.uuid4()

        # Mock search result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_project]
        mock_db_session.execute.return_value = mock_result

        result = await repo.search(tenant_id, "test", skip=0, limit=10)

        assert len(result) == 1
        assert result[0] == sample_project

    @pytest.mark.asyncio
    async def test_get_project_stats(self, mock_db_session, sample_project):
        """Test getting project statistics."""
        repo = ProjectRepository(mock_db_session)
        project_id = sample_project.id

        # Mock get_by_id
        with patch.object(repo, 'get_by_id', return_value=sample_project):
            # Mock statistics queries
            mock_requirements_result = Mock()
            mock_requirements_result.scalar.return_value = 10

            mock_members_result = Mock()
            mock_members_result.scalar.return_value = 3

            mock_db_session.execute.side_effect = [
                Mock(fetchall=Mock(return_value=[(RequirementStatus.DRAFT, 5), (RequirementStatus.APPROVED, 5)])),
                mock_requirements_result,
                mock_members_result
            ]

            result = await repo.get_project_stats(project_id)

            assert result['project_id'] == project_id
            assert result['total_requirements'] == 10
            assert result['members_count'] == 3
            assert 'requirements_by_status' in result


class TestProjectMemberRepository:
    """Test ProjectMemberRepository."""

    @pytest.mark.asyncio
    async def test_add_member(self, mock_db_session):
        """Test adding a project member."""
        repo = ProjectMemberRepository(mock_db_session)
        member = ProjectMember(
            project_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="developer"
        )

        # Mock flush and refresh
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await repo.add_member(member)

        assert result == member
        mock_db_session.add.assert_called_once_with(member)

    @pytest.mark.asyncio
    async def test_is_member(self, mock_db_session):
        """Test checking if user is project member."""
        repo = ProjectMemberRepository(mock_db_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock member exists
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role="developer"
        )
        mock_db_session.execute.return_value = mock_result

        result = await repo.is_member(project_id, user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_is_not_member(self, mock_db_session):
        """Test checking if user is not project member."""
        repo = ProjectMemberRepository(mock_db_session)
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock member does not exist
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await repo.is_member(project_id, user_id)

        assert result is False


class TestRequirementRepository:
    """Test RequirementRepository."""

    @pytest.mark.asyncio
    async def test_create_requirement(self, mock_db_session, sample_requirement):
        """Test creating a requirement."""
        repo = RequirementRepository(mock_db_session)

        # Mock flush and refresh
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await repo.create(sample_requirement)

        assert result == sample_requirement
        mock_db_session.add.assert_called_once_with(sample_requirement)

    @pytest.mark.asyncio
    async def test_get_by_project(self, mock_db_session, sample_requirement):
        """Test getting requirements by project."""
        repo = RequirementRepository(mock_db_session)
        project_id = uuid.uuid4()

        # Mock database result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_requirement]
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_by_project(project_id)

        assert len(result) == 1
        assert result[0] == sample_requirement

    @pytest.mark.asyncio
    async def test_get_by_identifier(self, mock_db_session, sample_requirement):
        """Test getting requirement by identifier."""
        repo = RequirementRepository(mock_db_session)
        project_id = uuid.uuid4()
        identifier = "REQ-0001"

        # Mock database result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_requirement
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_by_identifier(identifier, project_id)

        assert result == sample_requirement

    @pytest.mark.asyncio
    async def test_search_requirements(self, mock_db_session, sample_requirement):
        """Test searching requirements."""
        repo = RequirementRepository(mock_db_session)
        project_id = uuid.uuid4()

        # Mock search result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_requirement]
        mock_db_session.execute.return_value = mock_result

        result = await repo.search(project_id, "test", skip=0, limit=10)

        assert len(result) == 1
        assert result[0] == sample_requirement

    @pytest.mark.asyncio
    async def test_get_next_identifier_number(self, mock_db_session):
        """Test getting next identifier number."""
        repo = RequirementRepository(mock_db_session)
        project_id = uuid.uuid4()

        # Mock max number result
        mock_result = Mock()
        mock_result.scalar.return_value = 5
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_next_identifier_number(project_id, "REQ")

        assert result == 6

    @pytest.mark.asyncio
    async def test_get_next_identifier_number_no_existing(self, mock_db_session):
        """Test getting next identifier number when none exist."""
        repo = RequirementRepository(mock_db_session)
        project_id = uuid.uuid4()

        # Mock no existing requirements
        mock_result = Mock()
        mock_result.scalar.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_next_identifier_number(project_id, "REQ")

        assert result == 1

    @pytest.mark.asyncio
    async def test_get_requirement_stats(self, mock_db_session):
        """Test getting requirement statistics."""
        repo = RequirementRepository(mock_db_session)
        project_id = uuid.uuid4()

        # Mock statistics results
        status_result = Mock()
        status_result.fetchall.return_value = [(RequirementStatus.DRAFT, 3), (RequirementStatus.APPROVED, 2)]

        type_result = Mock()
        type_result.fetchall.return_value = [(RequirementType.FUNCTIONAL, 4), (RequirementType.NON_FUNCTIONAL, 1)]

        priority_result = Mock()
        priority_result.fetchall.return_value = [(Priority.HIGH, 2), (Priority.MEDIUM, 3)]

        story_points_result = Mock()
        story_points_result.scalar.return_value = 25

        business_value_result = Mock()
        business_value_result.scalar.return_value = 75.5

        mock_db_session.execute.side_effect = [
            status_result,
            type_result,
            priority_result,
            story_points_result,
            business_value_result
        ]

        result = await repo.get_requirement_stats(project_id)

        assert result['project_id'] == project_id
        assert result['status_counts'][RequirementStatus.DRAFT.value] == 3
        assert result['type_counts'][RequirementType.FUNCTIONAL.value] == 4
        assert result['priority_counts'][Priority.HIGH.value] == 2
        assert result['total_story_points'] == 25
        assert result['average_business_value'] == 75.5

    @pytest.mark.asyncio
    async def test_get_by_bounded_context(self, mock_db_session, sample_requirement):
        """Test getting requirements by bounded context."""
        repo = RequirementRepository(mock_db_session)
        project_id = uuid.uuid4()
        bounded_context = "User Management"

        # Mock database result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_requirement]
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_by_bounded_context(project_id, bounded_context)

        assert len(result) == 1
        assert result[0] == sample_requirement


class TestAcceptanceCriteriaRepository:
    """Test AcceptanceCriteriaRepository."""

    @pytest.mark.asyncio
    async def test_create_criteria(self, mock_db_session):
        """Test creating acceptance criteria."""
        repo = AcceptanceCriteriaRepository(mock_db_session)
        criteria = AcceptanceCriteria(
            requirement_id=uuid.uuid4(),
            description="User can login with valid credentials",
            order=1,
            created_by=uuid.uuid4()
        )

        # Mock flush and refresh
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await repo.create(criteria)

        assert result == criteria
        mock_db_session.add.assert_called_once_with(criteria)

    @pytest.mark.asyncio
    async def test_get_by_requirement(self, mock_db_session):
        """Test getting acceptance criteria by requirement."""
        repo = AcceptanceCriteriaRepository(mock_db_session)
        requirement_id = uuid.uuid4()

        criteria = AcceptanceCriteria(
            requirement_id=requirement_id,
            description="Test criteria",
            order=1,
            created_by=uuid.uuid4()
        )

        # Mock database result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [criteria]
        mock_db_session.execute.return_value = mock_result

        result = await repo.get_by_requirement(requirement_id)

        assert len(result) == 1
        assert result[0] == criteria

    @pytest.mark.asyncio
    async def test_delete_criteria(self, mock_db_session):
        """Test deleting acceptance criteria."""
        repo = AcceptanceCriteriaRepository(mock_db_session)
        criteria_id = uuid.uuid4()

        criteria = AcceptanceCriteria(
            id=criteria_id,
            requirement_id=uuid.uuid4(),
            description="Test criteria",
            order=1,
            created_by=uuid.uuid4()
        )

        # Mock finding criteria
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = criteria
        mock_db_session.execute.return_value = mock_result

        # Mock delete and flush
        mock_db_session.delete = AsyncMock()
        mock_db_session.flush = AsyncMock()

        result = await repo.delete(criteria_id)

        assert result is True
        mock_db_session.delete.assert_called_once_with(criteria)

    @pytest.mark.asyncio
    async def test_delete_criteria_not_found(self, mock_db_session):
        """Test deleting non-existent criteria."""
        repo = AcceptanceCriteriaRepository(mock_db_session)
        criteria_id = uuid.uuid4()

        # Mock criteria not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await repo.delete(criteria_id)

        assert result is False
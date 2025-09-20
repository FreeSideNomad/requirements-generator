"""
Integration tests for requirements API endpoints.
Tests the full request/response cycle with database operations.
"""

import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from src.requirements.models import RequirementType, RequirementStatus, Priority


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    return {
        "id": str(uuid.uuid4()),
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "full_name": "Test User",
        "is_active": True,
        "tenant_id": str(uuid.uuid4())
    }


@pytest.fixture
def mock_tenant():
    """Mock tenant."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Tenant",
        "subdomain": f"test_{uuid.uuid4().hex[:8]}",
        "plan": "premium",
        "is_active": True,
        "settings": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def auth_headers(mock_auth_user):
    """Create authentication headers."""
    # Mock JWT token
    return {"Authorization": "Bearer mock_jwt_token"}


@pytest.fixture
def sample_project_data():
    """Sample project creation data."""
    return {
        "name": "Test Project",
        "description": "Integration test project",
        "vision": "To test the API",
        "goals": ["Goal 1", "Goal 2"],
        "success_criteria": ["Success 1"],
        "stakeholders": [{"name": "John Doe", "role": "Product Owner"}],
        "methodology": "scrum",
        "domain_model": {"contexts": ["user", "payment"]},
        "is_template": False,
        "project_settings": {"feature_flags": {"ai_enabled": True}}
    }


@pytest.fixture
def sample_requirement_data():
    """Sample requirement creation data."""
    return {
        "title": "User Authentication",
        "description": "Users should be able to authenticate",
        "rationale": "Security requirement",
        "requirement_type": RequirementType.USER_STORY,
        "category": "Authentication",
        "tags": ["auth", "security"],
        "priority": Priority.HIGH,
        "complexity": "moderate",
        "user_persona": "End User",
        "user_goal": "authenticate securely",
        "user_benefit": "access my account safely",
        "story_points": 5,
        "estimated_hours": 20,
        "business_value": 85,
        "bounded_context": "User Management",
        "domain_entity": "User",
        "aggregate_root": "UserAccount",
        "custom_fields": {"priority_reason": "Security critical"},
        "source": "Security Review"
    }


class TestProjectEndpoints:
    """Test project-related API endpoints."""

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.create_project')
    def test_create_project_success(
        self,
        mock_create_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        sample_project_data,
        auth_headers
    ):
        """Test successful project creation."""
        # Setup mocks
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        # Mock service response
        project_response = {
            "id": str(uuid.uuid4()),
            "name": sample_project_data["name"],
            "description": sample_project_data["description"],
            "vision": sample_project_data["vision"],
            "goals": sample_project_data["goals"],
            "success_criteria": sample_project_data["success_criteria"],
            "stakeholders": sample_project_data["stakeholders"],
            "methodology": sample_project_data["methodology"],
            "domain_model": sample_project_data["domain_model"],
            "tenant_id": mock_tenant["id"],
            "created_by": mock_auth_user["id"],
            "is_active": True,
            "is_template": False,
            "project_settings": sample_project_data["project_settings"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "requirement_count": 0,
            "member_count": 1
        }

        mock_create_project.return_value = Mock(**project_response)

        # Make request
        response = test_client.post(
            "/api/requirements/projects",
            json=sample_project_data,
            headers=auth_headers
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_project_data["name"]
        assert data["methodology"] == sample_project_data["methodology"]
        assert data["requirement_count"] == 0
        assert data["member_count"] == 1

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    def test_create_project_validation_error(
        self,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test project creation with validation error."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        # Invalid data (missing required name)
        invalid_data = {"description": "Project without name"}

        response = test_client.post(
            "/api/requirements/projects",
            json=invalid_data,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_user_projects')
    def test_list_projects_success(
        self,
        mock_get_projects,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful project listing."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        # Mock projects
        mock_projects = [
            Mock(
                id=uuid.uuid4(),
                name="Project 1",
                description="First project",
                methodology="agile",
                is_active=True,
                is_template=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                requirements=[],
                members=[]
            ),
            Mock(
                id=uuid.uuid4(),
                name="Project 2",
                description="Second project",
                methodology="scrum",
                is_active=True,
                is_template=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                requirements=[],
                members=[]
            )
        ]

        mock_get_projects.return_value = (mock_projects, 2)

        response = test_client.get(
            "/api/requirements/projects?page=1&page_size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Project 1"
        assert data["items"][1]["name"] == "Project 2"
        assert data["has_next"] is False
        assert data["has_previous"] is False

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    def test_get_project_success(
        self,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful project retrieval."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        project_id = uuid.uuid4()
        mock_project = Mock(
            id=project_id,
            name="Test Project",
            description="Test description",
            vision="Test vision",
            goals=["Goal 1"],
            success_criteria=["Success 1"],
            stakeholders=[],
            methodology="agile",
            domain_model={},
            tenant_id=uuid.UUID(mock_tenant["id"]),
            created_by=uuid.UUID(mock_auth_user["id"]),
            is_active=True,
            is_template=False,
            project_settings={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            requirements=[],
            members=[]
        )

        mock_get_project.return_value = mock_project

        response = test_client.get(
            f"/api/requirements/projects/{project_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["methodology"] == "agile"

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    def test_get_project_not_found(
        self,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test project not found."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant
        mock_get_project.return_value = None

        project_id = uuid.uuid4()
        response = test_client.get(
            f"/api/requirements/projects/{project_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "PROJECT_NOT_FOUND"

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    def test_get_project_access_denied(
        self,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test project access denied (different tenant)."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        # Project belongs to different tenant
        mock_project = Mock(
            tenant_id=uuid.uuid4(),  # Different tenant
            is_active=True
        )
        mock_get_project.return_value = mock_project

        project_id = uuid.uuid4()
        response = test_client.get(
            f"/api/requirements/projects/{project_id}",
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "ACCESS_DENIED"


class TestRequirementEndpoints:
    """Test requirement-related API endpoints."""

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.service.RequirementService.create_requirement')
    def test_create_requirement_success(
        self,
        mock_create_requirement,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        sample_requirement_data,
        auth_headers
    ):
        """Test successful requirement creation."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        project_id = uuid.uuid4()
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"]),
            is_active=True
        )
        mock_get_project.return_value = mock_project

        # Mock requirement response
        requirement_response = Mock(
            id=uuid.uuid4(),
            project_id=project_id,
            identifier="US-001",
            title=sample_requirement_data["title"],
            description=sample_requirement_data["description"],
            requirement_type=sample_requirement_data["requirement_type"],
            status=RequirementStatus.DRAFT,
            priority=sample_requirement_data["priority"],
            story_points=sample_requirement_data["story_points"],
            children_count=0,
            acceptance_criteria_count=0
        )
        mock_create_requirement.return_value = requirement_response

        response = test_client.post(
            f"/api/requirements/projects/{project_id}/requirements",
            json=sample_requirement_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_requirement_data["title"]
        assert data["identifier"] == "US-001"
        assert data["story_points"] == 5

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    def test_create_requirement_project_not_found(
        self,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        sample_requirement_data,
        auth_headers
    ):
        """Test requirement creation with project not found."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant
        mock_get_project.return_value = None

        project_id = uuid.uuid4()
        response = test_client.post(
            f"/api/requirements/projects/{project_id}/requirements",
            json=sample_requirement_data,
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "PROJECT_NOT_FOUND"

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.service.RequirementService.get_project_requirements')
    def test_list_requirements_success(
        self,
        mock_get_requirements,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful requirements listing."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        project_id = uuid.uuid4()
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        # Mock requirements response
        mock_requirements_response = Mock(
            items=[
                {
                    "id": str(uuid.uuid4()),
                    "identifier": "US-001",
                    "title": "User Login",
                    "requirement_type": RequirementType.USER_STORY,
                    "status": RequirementStatus.DRAFT,
                    "priority": Priority.HIGH,
                    "complexity": "moderate",
                    "parent_id": None,
                    "story_points": 5,
                    "business_value": 80,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "created_by": mock_auth_user["id"],
                    "children_count": 0,
                    "acceptance_criteria_count": 2
                }
            ],
            total=1,
            page=1,
            page_size=20,
            pages=1,
            has_next=False,
            has_previous=False
        )
        mock_get_requirements.return_value = mock_requirements_response

        response = test_client.get(
            f"/api/requirements/projects/{project_id}/requirements?page=1&page_size=20",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["identifier"] == "US-001"

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.RequirementService.get_requirement')
    @patch('src.requirements.service.ProjectService.get_project')
    def test_get_requirement_success(
        self,
        mock_get_project,
        mock_get_requirement,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful requirement retrieval."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        requirement_id = uuid.uuid4()
        project_id = uuid.uuid4()

        mock_requirement = Mock(
            id=requirement_id,
            project_id=project_id,
            identifier="US-001",
            title="User Login",
            description="User authentication feature",
            requirement_type=RequirementType.USER_STORY,
            status=RequirementStatus.DRAFT,
            priority=Priority.HIGH
        )
        mock_get_requirement.return_value = mock_requirement

        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        response = test_client.get(
            f"/api/requirements/requirements/{requirement_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["identifier"] == "US-001"
        assert data["title"] == "User Login"

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.RequirementService.get_requirement')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.service.RequirementService.update_requirement')
    def test_update_requirement_success(
        self,
        mock_update_requirement,
        mock_get_project,
        mock_get_requirement,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful requirement update."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        requirement_id = uuid.uuid4()
        project_id = uuid.uuid4()

        # Mock existing requirement
        mock_existing_requirement = Mock(
            id=requirement_id,
            project_id=project_id
        )
        mock_get_requirement.return_value = mock_existing_requirement

        # Mock project
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        # Mock updated requirement
        mock_updated_requirement = Mock(
            id=requirement_id,
            title="Updated Title",
            status=RequirementStatus.APPROVED
        )
        mock_update_requirement.return_value = mock_updated_requirement

        update_data = {
            "title": "Updated Title",
            "status": RequirementStatus.APPROVED,
            "change_reason": "Stakeholder feedback"
        }

        response = test_client.put(
            f"/api/requirements/requirements/{requirement_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.RequirementService.get_requirement')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.service.RequirementService.delete_requirement')
    def test_delete_requirement_success(
        self,
        mock_delete_requirement,
        mock_get_project,
        mock_get_requirement,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful requirement deletion."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        requirement_id = uuid.uuid4()
        project_id = uuid.uuid4()

        # Mock existing requirement
        mock_existing_requirement = Mock(
            id=requirement_id,
            project_id=project_id
        )
        mock_get_requirement.return_value = mock_existing_requirement

        # Mock project
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        mock_delete_requirement.return_value = True

        response = test_client.delete(
            f"/api/requirements/requirements/{requirement_id}",
            headers=auth_headers
        )

        assert response.status_code == 204


class TestAcceptanceCriteriaEndpoints:
    """Test acceptance criteria API endpoints."""

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.RequirementService.get_requirement')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.service.RequirementService.create_acceptance_criteria')
    def test_create_acceptance_criteria_success(
        self,
        mock_create_criteria,
        mock_get_project,
        mock_get_requirement,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful acceptance criteria creation."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        requirement_id = uuid.uuid4()
        project_id = uuid.uuid4()

        # Mock requirement
        mock_requirement = Mock(
            id=requirement_id,
            project_id=project_id
        )
        mock_get_requirement.return_value = mock_requirement

        # Mock project
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        # Mock created criteria
        mock_criteria = Mock(
            id=uuid.uuid4(),
            requirement_id=requirement_id,
            title="Login Success",
            description="User should be redirected",
            given_when_then="Given valid creds, when login, then redirect",
            order_index=1,
            is_testable=True,
            test_status=None,
            test_notes=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=uuid.UUID(mock_auth_user["id"])
        )
        mock_create_criteria.return_value = mock_criteria

        criteria_data = {
            "title": "Login Success",
            "description": "User should be redirected",
            "given_when_then": "Given valid creds, when login, then redirect",
            "order_index": 1,
            "is_testable": True
        }

        response = test_client.post(
            f"/api/requirements/requirements/{requirement_id}/acceptance-criteria",
            json=criteria_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Login Success"
        assert data["requirement_id"] == str(requirement_id)


class TestDomainAnalysisEndpoints:
    """Test domain analysis API endpoints."""

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.service.DomainService.get_bounded_contexts')
    def test_get_bounded_contexts_success(
        self,
        mock_get_contexts,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful bounded contexts retrieval."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        project_id = uuid.uuid4()
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        mock_contexts = ["User Management", "Payment Processing", "Inventory"]
        mock_get_contexts.return_value = mock_contexts

        response = test_client.get(
            f"/api/requirements/projects/{project_id}/domain/contexts",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data == ["User Management", "Payment Processing", "Inventory"]

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.service.DomainService.analyze_domain_model')
    def test_analyze_domain_model_success(
        self,
        mock_analyze_domain,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful domain model analysis."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        project_id = uuid.uuid4()
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        mock_domain_model = {
            "User Management": {
                "entities": ["User", "Profile"],
                "aggregates": ["UserAccount"],
                "requirements": [
                    {
                        "id": str(uuid.uuid4()),
                        "identifier": "US-001",
                        "title": "User Login",
                        "type": "user_story"
                    }
                ]
            }
        }
        mock_analyze_domain.return_value = mock_domain_model

        response = test_client.get(
            f"/api/requirements/projects/{project_id}/domain/analysis",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "User Management" in data
        assert "User" in data["User Management"]["entities"]
        assert "UserAccount" in data["User Management"]["aggregates"]


class TestDocumentationGeneration:
    """Test documentation generation endpoints."""

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    @patch('src.requirements.markdown_generator.MarkdownGenerator.generate_project_documentation')
    def test_generate_markdown_documentation_success(
        self,
        mock_generate_docs,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test successful markdown documentation generation."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        project_id = uuid.uuid4()
        mock_project = Mock(
            id=project_id,
            name="Test Project",
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        mock_markdown_content = "# Test Project\n\nThis is the generated documentation."
        mock_generate_docs.return_value = mock_markdown_content

        format_config = {
            "format_type": "markdown",
            "include_children": True,
            "include_acceptance_criteria": True,
            "include_comments": False
        }

        response = test_client.post(
            f"/api/requirements/projects/{project_id}/documentation/generate",
            json=format_config,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "Test_Project_requirements.md" in response.headers.get("content-disposition", "")
        assert "Test Project" in response.text

    @patch('src.auth.routes.get_current_user_dependency')
    @patch('src.shared.dependencies.get_current_tenant')
    @patch('src.requirements.service.ProjectService.get_project')
    def test_generate_documentation_unsupported_format(
        self,
        mock_get_project,
        mock_get_tenant,
        mock_get_user,
        test_client,
        mock_auth_user,
        mock_tenant,
        auth_headers
    ):
        """Test documentation generation with unsupported format."""
        mock_get_user.return_value = mock_auth_user
        mock_get_tenant.return_value = mock_tenant

        project_id = uuid.uuid4()
        mock_project = Mock(
            id=project_id,
            tenant_id=uuid.UUID(mock_tenant["id"])
        )
        mock_get_project.return_value = mock_project

        format_config = {
            "format_type": "pdf",  # Unsupported format
            "include_children": True,
            "include_acceptance_criteria": True,
            "include_comments": False
        }

        response = test_client.post(
            f"/api/requirements/projects/{project_id}/documentation/generate",
            json=format_config,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "UNSUPPORTED_FORMAT"


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_requirements_health_check(self, test_client):
        """Test requirements service health check."""
        response = test_client.get("/api/requirements/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "requirements"


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization scenarios."""

    def test_create_project_without_auth(self, test_client, sample_project_data):
        """Test project creation without authentication."""
        response = test_client.post(
            "/api/requirements/projects",
            json=sample_project_data
        )

        assert response.status_code == 401

    def test_list_projects_without_auth(self, test_client):
        """Test project listing without authentication."""
        response = test_client.get("/api/requirements/projects")

        assert response.status_code == 401

    def test_get_project_without_auth(self, test_client):
        """Test project retrieval without authentication."""
        project_id = uuid.uuid4()
        response = test_client.get(f"/api/requirements/projects/{project_id}")

        assert response.status_code == 401
# Updated Technical Specifications - FastAPI + Pydantic Architecture

## Technology Stack Overview

### Core Framework Stack
```yaml
Backend_Framework:
  api: "FastAPI 0.104+"
  validation: "Pydantic v2"
  templates: "Jinja2 with HTMX"
  async_runtime: "asyncio with uvloop"
  type_checking: "mypy with strict mode"

Database_Layer:
  primary: "PostgreSQL 15+ with asyncpg"
  vector_extension: "pgvector for embeddings"
  migrations: "Alembic"
  connection_pooling: "asyncpg pool"

Real_Time_Communication:
  method: "Server-Sent Events (SSE)"
  user_queues: "Redis with async client"
  session_state: "Redis with JSON serialization"
  pub_sub: "Redis pub/sub for cross-node communication"

Authentication:
  method: "JWT with Azure AD integration"
  library: "python-jose[cryptography]"
  session_management: "Redis-backed sessions"
  token_validation: "Async Azure AD validation"
```

## Pydantic Data Models

### Core Business Models
```python
# models/base.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class BaseEntity(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="forbid"
    )

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# models/tenant.py
class IndustryType(str, Enum):
    BANKING = "banking"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    FINTECH = "fintech"
    GOVERNMENT = "government"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"

class JurisdictionType(str, Enum):
    CANADA = "canada"
    US = "us"
    EU = "eu"
    UK = "uk"
    AUSTRALIA = "australia"

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"

class BusinessContext(BaseModel):
    """Tenant-specific business context configuration"""
    industry: IndustryType
    jurisdiction: JurisdictionType
    company_size: str = Field(..., description="startup|sme|enterprise")
    compliance_requirements: List[str] = Field(default_factory=list)
    regulatory_frameworks: List[str] = Field(default_factory=list)
    custom_context: Dict[str, Any] = Field(default_factory=dict)

class TenantSettings(BaseModel):
    """Tenant configuration settings"""
    ai_tone: str = Field(default="professional", pattern="^(casual|professional|technical)$")
    question_depth: str = Field(default="detailed", pattern="^(basic|detailed|comprehensive)$")
    compliance_focus: bool = Field(default=True)
    auto_research: bool = Field(default=True)
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)

class Tenant(BaseEntity):
    name: str = Field(..., min_length=2, max_length=200)
    subdomain: str = Field(..., pattern="^[a-z0-9-]+$", min_length=3, max_length=50)
    industry_template_id: Optional[UUID] = None
    business_context: BusinessContext
    settings: TenantSettings = Field(default_factory=TenantSettings)
    status: TenantStatus = Field(default=TenantStatus.TRIAL)
    subscription_expires: Optional[datetime] = None

class IndustryTemplate(BaseEntity):
    name: str = Field(..., max_length=100)
    industry: IndustryType
    jurisdiction: JurisdictionType
    description: str = Field(..., max_length=500)
    template_data: Dict[str, Any] = Field(default_factory=dict)
    ai_prompts: Dict[str, str] = Field(default_factory=dict)
    domain_objects: List[str] = Field(default_factory=list)
    integration_patterns: List[str] = Field(default_factory=list)
    compliance_frameworks: List[str] = Field(default_factory=list)

# Request/Response models
class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    subdomain: str = Field(..., pattern="^[a-z0-9-]+$")
    business_context: BusinessContext
    settings: Optional[TenantSettings] = None

class TenantResponse(BaseModel):
    id: UUID
    name: str
    subdomain: str
    industry_template_id: Optional[UUID]
    business_context: BusinessContext
    settings: TenantSettings
    status: TenantStatus
    created_at: datetime
```

### Requirements Models with Pydantic
```python
# models/requirements.py
class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    COMPLIANCE = "compliance"
    BUSINESS_RULE = "business_rule"

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RequirementStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    ARCHIVED = "archived"

class Product(BaseEntity):
    tenant_id: UUID
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    vision: Optional[str] = Field(None, max_length=5000)
    business_context_override: Optional[Dict[str, Any]] = None
    teams: List[UUID] = Field(default_factory=list)

class Epic(BaseEntity):
    tenant_id: UUID
    product_id: UUID
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    business_value: str = Field(..., min_length=10, max_length=1000)
    acceptance_criteria: List[str] = Field(default_factory=list)
    bounded_contexts: List[str] = Field(default_factory=list)
    priority: Priority = Field(default=Priority.MEDIUM)
    status: RequirementStatus = Field(default=RequirementStatus.DRAFT)

class Feature(BaseEntity):
    tenant_id: UUID
    epic_id: UUID
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    functional_requirements: List[str] = Field(default_factory=list)
    non_functional_requirements: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    domain_objects: List[str] = Field(default_factory=list)
    priority: Priority = Field(default=Priority.MEDIUM)
    status: RequirementStatus = Field(default=RequirementStatus.DRAFT)

class UserStory(BaseEntity):
    tenant_id: UUID
    feature_id: UUID
    title: str = Field(..., min_length=10, max_length=200)
    as_a: str = Field(..., min_length=3, max_length=100, description="User type")
    i_want: str = Field(..., min_length=10, max_length=500, description="Capability")
    so_that: str = Field(..., min_length=10, max_length=500, description="Business value")
    acceptance_criteria: List[str] = Field(default_factory=list)
    estimated_effort: Optional[int] = Field(None, ge=1, le=100, description="Story points")
    priority: Priority = Field(default=Priority.MEDIUM)
    status: RequirementStatus = Field(default=RequirementStatus.DRAFT)

# Vector embeddings model
class RequirementEmbedding(BaseEntity):
    tenant_id: UUID
    requirement_type: str = Field(..., description="Product, Epic, Feature, UserStory")
    requirement_id: UUID
    text_content: str = Field(..., min_length=10)
    embedding_vector: Optional[List[float]] = None  # Will be populated by vector service
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Request/Response models
class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    vision: Optional[str] = Field(None, max_length=5000)

class EpicCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    business_value: str = Field(..., min_length=10, max_length=1000)
    priority: Priority = Field(default=Priority.MEDIUM)

class UserStoryCreateRequest(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    as_a: str = Field(..., min_length=3, max_length=100)
    i_want: str = Field(..., min_length=10, max_length=500)
    so_that: str = Field(..., min_length=10, max_length=500)
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: Priority = Field(default=Priority.MEDIUM)
```

### AI and Session Models
```python
# models/ai_session.py
class SessionType(str, Enum):
    VISION_DEFINITION = "vision_definition"
    EPIC_DISCOVERY = "epic_discovery"
    FEATURE_DETAILING = "feature_detailing"
    USER_STORY_CREATION = "user_story_creation"
    REQUIREMENT_REFINEMENT = "requirement_refinement"
    DOMAIN_MODELING = "domain_modeling"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"

class MessageType(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    ERROR = "error"

class ConversationSession(BaseEntity):
    tenant_id: UUID
    product_id: UUID
    session_type: SessionType
    title: str = Field(..., min_length=3, max_length=200)
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    participants: List[UUID] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime = Field(..., description="Session expiration time")

class ConversationMessage(BaseEntity):
    tenant_id: UUID
    session_id: UUID
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: MessageType
    author_id: Optional[UUID] = None  # None for AI messages
    metadata: Dict[str, Any] = Field(default_factory=dict)
    references_message_id: Optional[UUID] = None

class AIAnalysisRequest(BaseModel):
    session_id: UUID
    requirements_text: str = Field(..., min_length=10, max_length=10000)
    analysis_type: str = Field(default="comprehensive")
    include_research: bool = Field(default=True)
    focus_areas: List[str] = Field(default_factory=list)

class AIAnalysisResponse(BaseModel):
    event_id: UUID
    status: str = Field(default="processing")
    message: str
    estimated_completion: Optional[datetime] = None

class AIProgressUpdate(BaseModel):
    event_id: UUID
    step: str
    progress: int = Field(..., ge=0, le=100)
    message: str
    details: Optional[Dict[str, Any]] = None

class AIAnalysisResult(BaseModel):
    event_id: UUID
    session_id: UUID
    analysis: Dict[str, Any]
    research_findings: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    identified_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
```

### API Endpoints with Pydantic Validation

```python
# api/tenants.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from typing import List, Optional

router = APIRouter(prefix="/api/tenants", tags=["tenants"])

@router.post("/", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreateRequest,
    background_tasks: BackgroundTasks
) -> TenantResponse:
    """Create new tenant with industry template"""

    # Validate subdomain availability
    existing = await tenant_service.get_by_subdomain(tenant_data.subdomain)
    if existing:
        raise HTTPException(409, "Subdomain already taken")

    # Create tenant with AI-generated context
    tenant = await tenant_service.create_tenant(tenant_data)

    # Initialize tenant with industry template (background)
    background_tasks.add_task(
        tenant_service.initialize_tenant_template,
        tenant.id
    )

    return TenantResponse.model_validate(tenant)

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    tenant: Tenant = Depends(get_current_tenant)
) -> TenantResponse:
    """Get tenant details"""
    if tenant.id != tenant_id:
        raise HTTPException(403, "Access denied")

    return TenantResponse.model_validate(tenant)

@router.post("/{tenant_id}/sessions", response_model=ConversationSession)
async def create_session(
    tenant_id: UUID,
    session_data: dict,
    tenant: Tenant = Depends(get_current_tenant),
    user_id: UUID = Depends(get_current_user_id)
) -> ConversationSession:
    """Create new conversation session"""

    session_request = ConversationSessionCreateRequest(**session_data)
    session = await session_service.create_session(
        tenant_id=tenant_id,
        user_id=user_id,
        session_data=session_request
    )

    return session

@router.post("/{tenant_id}/analyze", response_model=AIAnalysisResponse)
async def analyze_requirements(
    tenant_id: UUID,
    analysis_request: AIAnalysisRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    user_id: UUID = Depends(get_current_user_id)
) -> AIAnalysisResponse:
    """Start async AI analysis of requirements"""

    event_id = uuid4()

    # Start background analysis
    background_tasks.add_task(
        ai_service.analyze_requirements_async,
        tenant_id=tenant_id,
        user_id=user_id,
        event_id=event_id,
        request=analysis_request
    )

    return AIAnalysisResponse(
        event_id=event_id,
        status="processing",
        message="Analysis started. You'll receive updates via events.",
        estimated_completion=datetime.utcnow() + timedelta(minutes=2)
    )

# API validation with Pydantic automatically handles:
# - Type checking and conversion
# - Input validation with detailed error messages
# - Request/response serialization
# - OpenAPI schema generation
# - Automatic API documentation
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Update vision and architecture documents with FastAPI decisions", "status": "completed", "activeForm": "Updating vision and architecture documents with FastAPI decisions"}, {"content": "Add Pydantic to technical specifications and data models", "status": "completed", "activeForm": "Adding Pydantic to technical specifications and data models"}, {"content": "Design session state management for multi-node deployment", "status": "in_progress", "activeForm": "Designing session state management for multi-node deployment"}, {"content": "Update all requirements documents with SaaS multi-tenant focus", "status": "pending", "activeForm": "Updating all requirements documents with SaaS multi-tenant focus"}]
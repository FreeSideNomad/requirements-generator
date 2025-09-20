"""
AI conversation Pydantic schemas for request/response validation.
Handles conversation sessions, messages, and AI interactions.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, validator

from .models import ConversationStatus, MessageType, MessageStatus


# Base Schemas
class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")
    description: Optional[str] = Field(None, description="Conversation description")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    model_name: str = Field(default="gpt-4", description="AI model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="AI temperature setting")
    max_tokens: Optional[int] = Field(None, gt=0, le=32000, description="Maximum tokens per response")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    template_id: Optional[uuid.UUID] = Field(None, description="Template to use for initialization")
    initial_message: Optional[str] = Field(None, description="Initial user message")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ConversationStatus] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=32000)
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime
    completed_at: Optional[datetime] = None
    message_count: Optional[int] = Field(None, description="Number of messages in conversation")


class ConversationListItem(BaseModel):
    """Schema for conversation list items."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    status: ConversationStatus
    created_at: datetime
    last_activity_at: datetime
    message_count: int = Field(0, description="Number of messages")
    model_name: str


# Message Schemas
class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1, description="Message content")
    message_type: MessageType = Field(default=MessageType.USER, description="Type of message")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    stream: bool = Field(default=True, description="Whether to stream the AI response")
    include_context: bool = Field(default=True, description="Include conversation context")


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: Optional[str] = Field(None, min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(MessageBase):
    """Schema for message responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    status: MessageStatus
    created_at: datetime
    processed_at: Optional[datetime] = None

    # Token usage
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    # Function calling
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


# AI Configuration Schemas
class AIModelConfigurationBase(BaseModel):
    """Base AI model configuration schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model_name: str = Field(..., description="OpenAI model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=32000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    system_instructions: Optional[str] = None
    function_calling_enabled: bool = Field(default=False)
    stream_enabled: bool = Field(default=True)


class AIModelConfigurationCreate(AIModelConfigurationBase):
    """Schema for creating AI model configuration."""
    pass


class AIModelConfigurationUpdate(BaseModel):
    """Schema for updating AI model configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=32000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    system_instructions: Optional[str] = None
    function_calling_enabled: Optional[bool] = None
    stream_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class AIModelConfigurationResponse(AIModelConfigurationBase):
    """Schema for AI model configuration responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Template Schemas
class ConversationTemplateBase(BaseModel):
    """Base conversation template schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=1)
    initial_message: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(default_factory=list)
    ai_model_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationTemplateCreate(ConversationTemplateBase):
    """Schema for creating conversation template."""
    pass


class ConversationTemplateUpdate(BaseModel):
    """Schema for updating conversation template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    initial_message: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    ai_model_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ConversationTemplateResponse(ConversationTemplateBase):
    """Schema for conversation template responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    created_by: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Streaming and Real-time Schemas
class StreamingMessageChunk(BaseModel):
    """Schema for streaming message chunks."""
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    is_complete: bool = Field(default=False)
    token_usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationEvent(BaseModel):
    """Schema for conversation events (SSE)."""
    event_type: str = Field(..., description="Type of event")
    conversation_id: uuid.UUID
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Batch Operations
class ConversationBatchOperation(BaseModel):
    """Schema for batch operations on conversations."""
    conversation_ids: List[uuid.UUID] = Field(..., min_items=1)
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Analytics and Reporting
class ConversationAnalytics(BaseModel):
    """Schema for conversation analytics."""
    total_conversations: int
    active_conversations: int
    total_messages: int
    total_tokens_used: int
    average_conversation_length: float
    most_used_models: List[Dict[str, Union[str, int]]]
    conversation_trends: List[Dict[str, Any]]


# Search and Filtering
class ConversationFilter(BaseModel):
    """Schema for conversation filtering."""
    status: Optional[ConversationStatus] = None
    model_name: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search_query: Optional[str] = Field(None, description="Search in title and messages")
    tags: Optional[List[str]] = None

    @validator('search_query')
    def validate_search_query(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('Search query must be at least 2 characters')
        return v.strip() if v else None


class PaginatedConversationResponse(BaseModel):
    """Paginated conversation response."""
    items: List[ConversationListItem]
    total: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    pages: int
    has_next: bool
    has_previous: bool
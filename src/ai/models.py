"""
AI conversation models using SQLAlchemy.
Handles conversation sessions, messages, and AI interactions.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..shared.models import BaseEntity

Base = declarative_base()


class ConversationStatus(str, Enum):
    """Conversation session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageType(str, Enum):
    """Message type in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class MessageStatus(str, Enum):
    """Message processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Conversation(Base):
    """AI conversation session model."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Tenant and user relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Conversation metadata
    status = Column(String(20), nullable=False, default=ConversationStatus.ACTIVE)
    context = Column(JSON, nullable=True)  # Additional context for AI
    system_prompt = Column(Text, nullable=True)  # Custom system prompt

    # AI configuration
    model_name = Column(String(100), nullable=False, default="gpt-4")
    temperature = Column(String(10), nullable=False, default="0.7")
    max_tokens = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.id}: {self.title}>"


class ConversationMessage(Base):
    """Individual message in a conversation."""

    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)

    # Message content
    message_type = Column(String(20), nullable=False)  # user, assistant, system, function
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # For OpenAI API compatibility

    # Message metadata
    status = Column(String(20), nullable=False, default=MessageStatus.COMPLETED)
    message_metadata = Column(JSON, nullable=True)  # Additional message metadata

    # Token usage tracking
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Function calling support
    function_call = Column(JSON, nullable=True)
    tool_calls = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ConversationMessage {self.id}: {self.message_type}>"


class ConversationTemplate(Base):
    """Pre-defined conversation templates for different use cases."""

    __tablename__ = "conversation_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Template configuration
    system_prompt = Column(Text, nullable=False)
    initial_message = Column(Text, nullable=True)
    model_config = Column(JSON, nullable=True)  # Default AI model configuration

    # Template metadata
    category = Column(String(100), nullable=True)  # e.g., "requirements", "planning", "analysis"
    tags = Column(JSON, nullable=True)  # Array of tags
    is_active = Column(Boolean, nullable=False, default=True)

    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # Null for global templates
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ConversationTemplate {self.id}: {self.name}>"


class AIModelConfiguration(Base):
    """AI model configuration presets."""

    __tablename__ = "ai_model_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Model settings
    model_name = Column(String(100), nullable=False)
    temperature = Column(String(10), nullable=False, default="0.7")
    max_tokens = Column(Integer, nullable=True)
    top_p = Column(String(10), nullable=True)
    frequency_penalty = Column(String(10), nullable=True)
    presence_penalty = Column(String(10), nullable=True)

    # Advanced configuration
    system_instructions = Column(Text, nullable=True)
    function_calling_enabled = Column(Boolean, nullable=False, default=False)
    stream_enabled = Column(Boolean, nullable=False, default=True)

    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AIModelConfiguration {self.id}: {self.name}>"
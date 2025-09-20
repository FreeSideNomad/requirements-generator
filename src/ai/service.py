"""
AI conversation service for OpenAI integration.
Handles conversation management, message processing, and AI interactions.
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator

import openai
from openai import AsyncOpenAI
import structlog

from ..config import settings
from ..shared.exceptions import ValidationError, NotFoundError, AppException
from .models import (
    Conversation, ConversationMessage, ConversationTemplate,
    AIModelConfiguration, ConversationStatus, MessageType, MessageStatus
)
from .schemas import (
    ConversationCreate, ConversationUpdate, MessageCreate,
    StreamingMessageChunk, ConversationEvent, ConversationResponse
)

logger = structlog.get_logger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions."""

    def __init__(self):
        """Initialize OpenAI service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.default_model = settings.openai_default_model
        self.max_retries = 3
        self.timeout = 60

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """Create a chat completion using OpenAI API."""
        try:
            model = model or self.default_model

            completion_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **kwargs
            }

            if max_tokens:
                completion_kwargs["max_tokens"] = max_tokens

            logger.info(
                "Creating chat completion",
                model=model,
                message_count=len(messages),
                stream=stream,
                temperature=temperature
            )

            response = await self.client.chat.completions.create(**completion_kwargs)

            return response

        except openai.APIError as e:
            logger.error("OpenAI API error", error=str(e), status_code=getattr(e, 'status_code', None))
            raise AppException(
                message=f"AI service error: {str(e)}",
                error_code="AI_API_ERROR",
                status_code=500
            )
        except Exception as e:
            logger.error("Unexpected error in OpenAI service", error=str(e))
            raise AppException(
                message="AI service temporarily unavailable",
                error_code="AI_SERVICE_ERROR",
                status_code=503
            )

    async def create_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Create a streaming chat completion."""
        try:
            stream = await self.create_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "is_complete": False,
                        "token_usage": None
                    }

                # Handle completion
                if chunk.choices[0].finish_reason is not None:
                    yield {
                        "content": "",
                        "is_complete": True,
                        "finish_reason": chunk.choices[0].finish_reason,
                        "token_usage": getattr(chunk, 'usage', None)
                    }

        except Exception as e:
            logger.error("Error in streaming completion", error=str(e))
            yield {
                "content": "",
                "is_complete": True,
                "error": str(e)
            }

    def format_messages_for_openai(self, messages: List[ConversationMessage]) -> List[Dict[str, str]]:
        """Format conversation messages for OpenAI API."""
        formatted_messages = []

        for message in messages:
            formatted_messages.append({
                "role": message.role,
                "content": message.content
            })

            # Add function call information if present
            if message.function_call:
                formatted_messages[-1]["function_call"] = message.function_call

            if message.tool_calls:
                formatted_messages[-1]["tool_calls"] = message.tool_calls

        return formatted_messages


class ConversationService:
    """Service for managing AI conversations."""

    def __init__(self, db_session=None):
        """Initialize conversation service."""
        self.db_session = db_session
        self.openai_service = OpenAIService()

    async def create_conversation(
        self,
        conversation_data: ConversationCreate,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> ConversationResponse:
        """Create a new conversation."""
        try:
            # Create conversation instance
            conversation = Conversation(
                title=conversation_data.title,
                description=conversation_data.description,
                user_id=user_id,
                tenant_id=tenant_id,
                system_prompt=conversation_data.system_prompt,
                model_name=conversation_data.model_name,
                temperature=str(conversation_data.temperature),
                max_tokens=conversation_data.max_tokens,
                context=conversation_data.context or {}
            )

            # Apply template if specified
            if conversation_data.template_id:
                template = await self.get_conversation_template(conversation_data.template_id)
                if template:
                    conversation.system_prompt = template.system_prompt
                    if template.model_config:
                        conversation.model_name = template.model_config.get("model_name", conversation.model_name)
                        conversation.temperature = str(template.model_config.get("temperature", conversation_data.temperature))

            # Save conversation
            # Note: This would need actual database session implementation
            # self.db_session.add(conversation)
            # await self.db_session.commit()

            logger.info(
                "Created new conversation",
                conversation_id=conversation.id,
                user_id=user_id,
                tenant_id=tenant_id,
                title=conversation.title
            )

            # Add system message if system prompt is provided
            if conversation.system_prompt:
                await self.add_system_message(conversation.id, conversation.system_prompt)

            # Add initial message if provided
            if conversation_data.initial_message:
                await self.add_message(
                    conversation.id,
                    MessageCreate(
                        content=conversation_data.initial_message,
                        message_type=MessageType.USER
                    ),
                    user_id=user_id
                )

            return ConversationResponse(
                id=conversation.id,
                title=conversation.title,
                description=conversation.description,
                user_id=conversation.user_id,
                tenant_id=conversation.tenant_id,
                status=conversation.status,
                system_prompt=conversation.system_prompt,
                model_name=conversation.model_name,
                temperature=float(conversation.temperature),
                max_tokens=conversation.max_tokens,
                context=conversation.context,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                last_activity_at=conversation.last_activity_at,
                completed_at=conversation.completed_at
            )

        except Exception as e:
            logger.error("Error creating conversation", error=str(e))
            raise AppException(
                message="Failed to create conversation",
                error_code="CONVERSATION_CREATE_ERROR",
                status_code=500
            )

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        message_data: MessageCreate,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Add a message to conversation and generate AI response."""
        try:
            # Get conversation
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise NotFoundError("Conversation not found")

            # Create user message
            user_message = ConversationMessage(
                conversation_id=conversation_id,
                message_type=MessageType.USER,
                content=message_data.content,
                role="user",
                status=MessageStatus.COMPLETED,
                message_metadata=message_data.metadata or {}
            )

            # Save user message
            # self.db_session.add(user_message)
            # await self.db_session.commit()

            logger.info(
                "Added user message",
                conversation_id=conversation_id,
                message_id=user_message.id,
                user_id=user_id
            )

            # Generate AI response if streaming is requested
            if message_data.stream:
                return await self.generate_streaming_response(conversation, user_message)
            else:
                return await self.generate_response(conversation, user_message)

        except Exception as e:
            logger.error("Error adding message", error=str(e), conversation_id=conversation_id)
            raise AppException(
                message="Failed to add message",
                error_code="MESSAGE_ADD_ERROR",
                status_code=500
            )

    async def generate_response(
        self,
        conversation: Conversation,
        user_message: ConversationMessage
    ) -> Dict[str, Any]:
        """Generate AI response for a conversation."""
        try:
            # Get conversation history
            messages = await self.get_conversation_messages(conversation.id)

            # Format messages for OpenAI
            formatted_messages = self.openai_service.format_messages_for_openai(messages)

            # Create AI response
            response = await self.openai_service.create_chat_completion(
                messages=formatted_messages,
                model=conversation.model_name,
                temperature=float(conversation.temperature),
                max_tokens=conversation.max_tokens,
                stream=False
            )

            # Extract response content
            ai_content = response.choices[0].message.content
            usage = response.usage

            # Create AI message
            ai_message = ConversationMessage(
                conversation_id=conversation.id,
                message_type=MessageType.ASSISTANT,
                content=ai_content,
                role="assistant",
                status=MessageStatus.COMPLETED,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                total_tokens=usage.total_tokens if usage else None,
                processed_at=datetime.utcnow()
            )

            # Save AI message
            # self.db_session.add(ai_message)
            # await self.db_session.commit()

            # Update conversation activity
            conversation.last_activity_at = datetime.utcnow()
            # await self.db_session.commit()

            logger.info(
                "Generated AI response",
                conversation_id=conversation.id,
                message_id=ai_message.id,
                tokens_used=usage.total_tokens if usage else None
            )

            return {
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "created_at": user_message.created_at
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "created_at": ai_message.created_at,
                    "token_usage": {
                        "prompt_tokens": ai_message.prompt_tokens,
                        "completion_tokens": ai_message.completion_tokens,
                        "total_tokens": ai_message.total_tokens
                    }
                }
            }

        except Exception as e:
            logger.error("Error generating AI response", error=str(e))
            raise AppException(
                message="Failed to generate AI response",
                error_code="AI_RESPONSE_ERROR",
                status_code=500
            )

    async def generate_streaming_response(
        self,
        conversation: Conversation,
        user_message: ConversationMessage
    ) -> AsyncGenerator[StreamingMessageChunk, None]:
        """Generate streaming AI response for a conversation."""
        try:
            # Get conversation history
            messages = await self.get_conversation_messages(conversation.id)

            # Format messages for OpenAI
            formatted_messages = self.openai_service.format_messages_for_openai(messages)

            # Create AI message placeholder
            ai_message = ConversationMessage(
                conversation_id=conversation.id,
                message_type=MessageType.ASSISTANT,
                content="",
                role="assistant",
                status=MessageStatus.PROCESSING
            )

            # Save placeholder
            # self.db_session.add(ai_message)
            # await self.db_session.commit()

            complete_content = ""

            # Stream AI response
            async for chunk in self.openai_service.create_streaming_completion(
                messages=formatted_messages,
                model=conversation.model_name,
                temperature=float(conversation.temperature),
                max_tokens=conversation.max_tokens
            ):
                if chunk.get("content"):
                    complete_content += chunk["content"]

                # Yield streaming chunk
                yield StreamingMessageChunk(
                    conversation_id=conversation.id,
                    message_id=ai_message.id,
                    content=chunk.get("content", ""),
                    is_complete=chunk.get("is_complete", False),
                    token_usage=chunk.get("token_usage")
                )

                # Handle completion
                if chunk.get("is_complete"):
                    # Update AI message with complete content
                    ai_message.content = complete_content
                    ai_message.status = MessageStatus.COMPLETED
                    ai_message.processed_at = datetime.utcnow()

                    if chunk.get("token_usage"):
                        usage = chunk["token_usage"]
                        ai_message.prompt_tokens = usage.get("prompt_tokens")
                        ai_message.completion_tokens = usage.get("completion_tokens")
                        ai_message.total_tokens = usage.get("total_tokens")

                    # Update conversation activity
                    conversation.last_activity_at = datetime.utcnow()

                    # Save updates
                    # await self.db_session.commit()

                    logger.info(
                        "Completed streaming AI response",
                        conversation_id=conversation.id,
                        message_id=ai_message.id,
                        total_tokens=ai_message.total_tokens
                    )

        except Exception as e:
            logger.error("Error in streaming response", error=str(e))
            yield StreamingMessageChunk(
                conversation_id=conversation.id,
                message_id=ai_message.id if 'ai_message' in locals() else uuid.uuid4(),
                content="",
                is_complete=True,
                metadata={"error": str(e)}
            )

    async def get_conversation(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        # This would need actual database implementation
        # return await self.db_session.query(Conversation).filter(Conversation.id == conversation_id).first()
        pass

    async def get_conversation_messages(self, conversation_id: uuid.UUID) -> List[ConversationMessage]:
        """Get all messages for a conversation."""
        # This would need actual database implementation
        # return await self.db_session.query(ConversationMessage).filter(
        #     ConversationMessage.conversation_id == conversation_id
        # ).order_by(ConversationMessage.created_at).all()
        return []

    async def get_conversation_template(self, template_id: uuid.UUID) -> Optional[ConversationTemplate]:
        """Get conversation template by ID."""
        # This would need actual database implementation
        # return await self.db_session.query(ConversationTemplate).filter(
        #     ConversationTemplate.id == template_id
        # ).first()
        pass

    async def add_system_message(self, conversation_id: uuid.UUID, content: str) -> ConversationMessage:
        """Add a system message to conversation."""
        system_message = ConversationMessage(
            conversation_id=conversation_id,
            message_type=MessageType.SYSTEM,
            content=content,
            role="system",
            status=MessageStatus.COMPLETED
        )

        # Save system message
        # self.db_session.add(system_message)
        # await self.db_session.commit()

        return system_message

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        update_data: ConversationUpdate,
        user_id: uuid.UUID
    ) -> ConversationResponse:
        """Update an existing conversation."""
        # This would need actual database implementation
        pass

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a conversation."""
        # This would need actual database implementation
        pass
"""
AI conversation FastAPI routes for conversation management and real-time interactions.
Handles conversation CRUD operations, message processing, and Server-Sent Events streaming.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..auth.routes import get_current_user_dependency as get_current_user
from ..auth.schemas import UserResponse
from ..shared.exceptions import ValidationError, NotFoundError, AppException
from ..shared.dependencies import get_db_session, get_current_tenant
from ..tenants.schemas import TenantResponse
from .service import ConversationService
from .schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse, ConversationListItem,
    ConversationFilter, PaginatedConversationResponse,
    StreamingMessageChunk, ConversationEvent,
    ConversationTemplateCreate, ConversationTemplateResponse,
    AIModelConfigurationCreate, AIModelConfigurationResponse
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> ConversationResponse:
    """Create a new AI conversation session."""
    try:
        conversation_service = ConversationService(db_session)

        conversation = await conversation_service.create_conversation(
            conversation_data=conversation_data,
            user_id=current_user.id,
            tenant_id=current_tenant.id
        )

        logger.info(
            "Created new conversation",
            conversation_id=conversation.id,
            user_id=current_user.id,
            tenant_id=current_tenant.id
        )

        return conversation

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error("Error creating conversation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CONVERSATION_CREATE_ERROR", "message": "Failed to create conversation"}
        )


@router.get("/conversations", response_model=PaginatedConversationResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by conversation status"),
    search: Optional[str] = Query(None, description="Search in conversation titles"),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> PaginatedConversationResponse:
    """List conversations for the current user and tenant."""
    try:
        # This would need actual implementation with database queries
        # For now, return empty paginated response
        return PaginatedConversationResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            pages=0,
            has_next=False,
            has_previous=False
        )

    except Exception as e:
        logger.error("Error listing conversations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CONVERSATION_LIST_ERROR", "message": "Failed to list conversations"}
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> ConversationResponse:
    """Get a specific conversation by ID."""
    try:
        conversation_service = ConversationService(db_session)
        conversation = await conversation_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}
            )

        # Check if user has access to this conversation
        if conversation.user_id != current_user.id or conversation.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to conversation"}
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting conversation", error=str(e), conversation_id=conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CONVERSATION_GET_ERROR", "message": "Failed to get conversation"}
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    update_data: ConversationUpdate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> ConversationResponse:
    """Update a conversation."""
    try:
        conversation_service = ConversationService(db_session)

        conversation = await conversation_service.update_conversation(
            conversation_id=conversation_id,
            update_data=update_data,
            user_id=current_user.id
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}
            )

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating conversation", error=str(e), conversation_id=conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CONVERSATION_UPDATE_ERROR", "message": "Failed to update conversation"}
        )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> None:
    """Delete a conversation."""
    try:
        conversation_service = ConversationService(db_session)

        success = await conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}
            )

        logger.info("Deleted conversation", conversation_id=conversation_id, user_id=current_user.id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting conversation", error=str(e), conversation_id=conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CONVERSATION_DELETE_ERROR", "message": "Failed to delete conversation"}
        )


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Send a message to a conversation and get AI response."""
    try:
        conversation_service = ConversationService(db_session)

        # Verify conversation exists and user has access
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}
            )

        if conversation.user_id != current_user.id or conversation.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to conversation"}
            )

        # Add message and generate response
        if message_data.stream:
            # For streaming, return message ID immediately and process in background
            user_message_id = uuid.uuid4()

            # Process streaming response in background
            background_tasks.add_task(
                process_streaming_message,
                conversation_service,
                conversation_id,
                message_data,
                current_user.id,
                user_message_id
            )

            return {
                "message_id": user_message_id,
                "conversation_id": conversation_id,
                "streaming": True,
                "status": "processing"
            }
        else:
            # Synchronous response
            response = await conversation_service.add_message(
                conversation_id=conversation_id,
                message_data=message_data,
                user_id=current_user.id
            )

            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending message", error=str(e), conversation_id=conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "MESSAGE_SEND_ERROR", "message": "Failed to send message"}
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> List[MessageResponse]:
    """Get messages for a conversation."""
    try:
        conversation_service = ConversationService(db_session)

        # Verify conversation exists and user has access
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}
            )

        if conversation.user_id != current_user.id or conversation.tenant_id != current_tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_DENIED", "message": "Access denied to conversation"}
            )

        messages = await conversation_service.get_conversation_messages(conversation_id)

        # Convert to response format
        message_responses = []
        for msg in messages:
            message_responses.append(MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                content=msg.content,
                message_type=msg.message_type,
                role=msg.role,
                status=msg.status,
                created_at=msg.created_at,
                processed_at=msg.processed_at,
                prompt_tokens=msg.prompt_tokens,
                completion_tokens=msg.completion_tokens,
                total_tokens=msg.total_tokens,
                function_call=msg.function_call,
                tool_calls=msg.tool_calls,
                metadata=msg.message_metadata or {}
            ))

        return message_responses[offset:offset + limit]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting messages", error=str(e), conversation_id=conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "MESSAGE_GET_ERROR", "message": "Failed to get messages"}
        )


@router.get("/conversations/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> EventSourceResponse:
    """Server-Sent Events stream for real-time conversation updates."""

    async def event_stream():
        """Generate SSE events for conversation updates."""
        try:
            # Verify conversation access
            conversation_service = ConversationService(db_session)
            conversation = await conversation_service.get_conversation(conversation_id)

            if not conversation:
                yield {
                    "event": "error",
                    "data": {"error": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}
                }
                return

            if conversation.user_id != current_user.id or conversation.tenant_id != current_tenant.id:
                yield {
                    "event": "error",
                    "data": {"error": "ACCESS_DENIED", "message": "Access denied to conversation"}
                }
                return

            # Send initial connection event
            yield {
                "event": "connected",
                "data": {
                    "conversation_id": str(conversation_id),
                    "user_id": str(current_user.id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            # Keep connection alive and send periodic heartbeats
            # In a real implementation, you would listen for Redis pub/sub events
            # or database changes to push real-time updates
            import asyncio
            while True:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                yield {
                    "event": "heartbeat",
                    "data": {"timestamp": datetime.utcnow().isoformat()}
                }

        except Exception as e:
            logger.error("Error in conversation stream", error=str(e), conversation_id=conversation_id)
            yield {
                "event": "error",
                "data": {"error": "STREAM_ERROR", "message": "Stream connection failed"}
            }

    return EventSourceResponse(event_stream())


# Template Management Routes

@router.get("/templates", response_model=List[ConversationTemplateResponse])
async def list_conversation_templates(
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> List[ConversationTemplateResponse]:
    """List available conversation templates."""
    # This would need actual database implementation
    return []


@router.post("/templates", response_model=ConversationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation_template(
    template_data: ConversationTemplateCreate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> ConversationTemplateResponse:
    """Create a new conversation template."""
    # This would need actual implementation
    raise HTTPException(status_code=501, detail="Not implemented")


# AI Model Configuration Routes

@router.get("/models", response_model=List[AIModelConfigurationResponse])
async def list_ai_models(
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> List[AIModelConfigurationResponse]:
    """List available AI model configurations."""
    # This would need actual database implementation
    return []


@router.post("/models", response_model=AIModelConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_model_config(
    model_data: AIModelConfigurationCreate,
    current_user: UserResponse = Depends(get_current_user),
    current_tenant: TenantResponse = Depends(get_current_tenant),
    db_session = Depends(get_db_session)
) -> AIModelConfigurationResponse:
    """Create a new AI model configuration."""
    # This would need actual implementation
    raise HTTPException(status_code=501, detail="Not implemented")


async def process_streaming_message(
    conversation_service: ConversationService,
    conversation_id: uuid.UUID,
    message_data: MessageCreate,
    user_id: uuid.UUID,
    user_message_id: uuid.UUID
) -> None:
    """Background task to process streaming message responses."""
    try:
        logger.info("Processing streaming message", conversation_id=conversation_id, user_id=user_id)

        # This would integrate with Redis pub/sub or other real-time mechanism
        # to send streaming chunks to the SSE endpoint

        # Get conversation and process message
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            logger.error("Conversation not found for streaming", conversation_id=conversation_id)
            return

        # Add message and get streaming response
        response = await conversation_service.add_message(
            conversation_id=conversation_id,
            message_data=message_data,
            user_id=user_id
        )

        # In a real implementation, this would publish to Redis for SSE consumption
        logger.info("Streaming message processed", conversation_id=conversation_id, user_id=user_id)

    except Exception as e:
        logger.error(
            "Error processing streaming message",
            error=str(e),
            conversation_id=conversation_id,
            user_id=user_id
        )


# Health check for AI service
@router.get("/health")
async def ai_health_check() -> Dict[str, str]:
    """Health check for AI service."""
    return {"status": "healthy", "service": "ai"}
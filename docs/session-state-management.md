# Session State Management for Multi-Node Deployment

## Problem Statement

With multiple FastAPI application nodes deployed for high availability and load balancing, we need to ensure:
- **Session persistence** across server restarts and load balancer routing
- **Real-time event delivery** to users regardless of which node they connect to
- **Consistent user state** when requests hit different nodes
- **Efficient session cleanup** and memory management

## Recommended Solution: Redis-Based Session Management

### Architecture Overview
```yaml
Session_Architecture:
  session_store: "Redis with JSON serialization"
  event_delivery: "Redis Pub/Sub for cross-node communication"
  user_queues: "Redis Streams for per-user SSE events"
  load_balancing: "Sticky sessions NOT required"
  session_expiry: "TTL-based automatic cleanup"
```

### Session State Models
```python
# models/session_state.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

class UserSessionState(BaseModel):
    """Complete user session state stored in Redis"""
    user_id: UUID
    tenant_id: UUID
    session_id: str  # HTTP session identifier

    # Authentication state
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: datetime

    # User preferences and context
    current_product_id: Optional[UUID] = None
    current_conversation_id: Optional[UUID] = None
    ui_preferences: Dict[str, Any] = Field(default_factory=dict)

    # Active operations tracking
    active_ai_operations: List[UUID] = Field(default_factory=list)
    pending_notifications: List[Dict[str, Any]] = Field(default_factory=list)

    # Session metadata
    last_activity: datetime
    ip_address: str
    user_agent: str
    created_at: datetime

class ConversationSessionState(BaseModel):
    """Conversation-specific state for AI interactions"""
    session_id: UUID
    tenant_id: UUID
    product_id: UUID

    # Conversation context
    message_count: int = 0
    last_ai_response: Optional[str] = None
    context_summary: str = ""

    # AI processing state
    pending_ai_requests: List[UUID] = Field(default_factory=list)
    rag_context_cache: Dict[str, Any] = Field(default_factory=dict)

    # Participants and permissions
    active_participants: List[UUID] = Field(default_factory=list)
    participant_permissions: Dict[str, str] = Field(default_factory=dict)

    # Session lifecycle
    expires_at: datetime
    last_message_at: Optional[datetime] = None

class SSEConnectionState(BaseModel):
    """Server-Sent Events connection tracking"""
    connection_id: str
    user_id: UUID
    tenant_id: UUID
    connected_at: datetime
    last_heartbeat: datetime
    subscribed_events: List[str] = Field(default_factory=list)
    node_id: str  # Which application node handles this connection
```

### Redis Session Service Implementation
```python
# services/session_service.py
import redis.asyncio as redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

class SessionService:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_SESSION_DB,  # Separate DB for sessions
            decode_responses=True
        )
        self.session_ttl = timedelta(hours=8)  # 8-hour session timeout
        self.conversation_ttl = timedelta(hours=4)  # 4-hour conversation timeout

    async def create_user_session(
        self,
        user_id: UUID,
        tenant_id: UUID,
        access_token: str,
        ip_address: str,
        user_agent: str
    ) -> str:
        """Create new user session and return session ID"""

        session_id = str(uuid.uuid4())

        session_state = UserSessionState(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            access_token=access_token,
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            last_activity=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )

        # Store in Redis with TTL
        await self.redis.setex(
            f"session:{session_id}",
            int(self.session_ttl.total_seconds()),
            session_state.model_dump_json()
        )

        # Track user's active sessions
        await self.redis.sadd(f"user_sessions:{user_id}", session_id)
        await self.redis.expire(f"user_sessions:{user_id}", int(self.session_ttl.total_seconds()))

        return session_id

    async def get_user_session(self, session_id: str) -> Optional[UserSessionState]:
        """Retrieve user session state"""

        session_data = await self.redis.get(f"session:{session_id}")
        if not session_data:
            return None

        try:
            return UserSessionState.model_validate_json(session_data)
        except Exception:
            # Invalid session data, cleanup
            await self.redis.delete(f"session:{session_id}")
            return None

    async def update_user_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update specific fields in user session"""

        session = await self.get_user_session(session_id)
        if not session:
            return False

        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.last_activity = datetime.utcnow()

        # Save back to Redis
        await self.redis.setex(
            f"session:{session_id}",
            int(self.session_ttl.total_seconds()),
            session.model_dump_json()
        )

        return True

    async def create_conversation_session(
        self,
        session_id: UUID,
        tenant_id: UUID,
        product_id: UUID,
        expires_at: datetime
    ) -> bool:
        """Create conversation session state"""

        conv_state = ConversationSessionState(
            session_id=session_id,
            tenant_id=tenant_id,
            product_id=product_id,
            expires_at=expires_at
        )

        await self.redis.setex(
            f"conversation:{session_id}",
            int(self.conversation_ttl.total_seconds()),
            conv_state.model_dump_json()
        )

        return True

    async def add_conversation_participant(
        self,
        session_id: UUID,
        user_id: UUID,
        permission_level: str = "participant"
    ) -> bool:
        """Add participant to conversation session"""

        conv_state = await self.get_conversation_session(session_id)
        if not conv_state:
            return False

        if user_id not in conv_state.active_participants:
            conv_state.active_participants.append(user_id)

        conv_state.participant_permissions[str(user_id)] = permission_level

        await self.redis.setex(
            f"conversation:{session_id}",
            int(self.conversation_ttl.total_seconds()),
            conv_state.model_dump_json()
        )

        return True

    async def get_conversation_session(self, session_id: UUID) -> Optional[ConversationSessionState]:
        """Get conversation session state"""

        conv_data = await self.redis.get(f"conversation:{session_id}")
        if not conv_data:
            return None

        try:
            return ConversationSessionState.model_validate_json(conv_data)
        except Exception:
            await self.redis.delete(f"conversation:{session_id}")
            return None

    async def cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions"""

        # Redis TTL handles most cleanup automatically
        # This handles orphaned references

        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match="user_sessions:*",
                count=100
            )

            for key in keys:
                sessions = await self.redis.smembers(key)
                for session_id in sessions:
                    exists = await self.redis.exists(f"session:{session_id}")
                    if not exists:
                        await self.redis.srem(key, session_id)

            if cursor == 0:
                break
```

### Multi-Node Event Distribution
```python
# services/event_service.py
class EventService:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_EVENTS_DB,
            decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
        self.node_id = f"node-{uuid.uuid4().hex[:8]}"

    async def publish_user_event(
        self,
        tenant_id: UUID,
        user_id: UUID,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Publish event to user across all nodes"""

        event = {
            "event_id": str(uuid.uuid4()),
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "event_type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
            "source_node": self.node_id
        }

        # Store in user's event stream
        await self.redis.xadd(
            f"events:{tenant_id}:{user_id}",
            event,
            maxlen=1000,  # Keep last 1000 events
            approximate=True
        )

        # Set expiry for the stream
        await self.redis.expire(f"events:{tenant_id}:{user_id}", 3600)  # 1 hour

        # Publish to all nodes for SSE connections
        await self.redis.publish(
            f"user_events:{tenant_id}:{user_id}",
            json.dumps(event)
        )

    async def get_user_events_since(
        self,
        tenant_id: UUID,
        user_id: UUID,
        since_id: str = "0"
    ) -> List[Dict[str, Any]]:
        """Get user events since specific ID"""

        stream_key = f"events:{tenant_id}:{user_id}"

        try:
            events = await self.redis.xread(
                {stream_key: since_id},
                count=50,
                block=30000  # 30-second timeout
            )

            if events:
                stream_events = events[0][1]  # First stream's events
                return [
                    {
                        "id": event_id,
                        **event_data
                    }
                    for event_id, event_data in stream_events
                ]

            return []

        except Exception:
            return []

    async def subscribe_to_user_events(self, tenant_id: UUID, user_id: UUID):
        """Subscribe to user events for SSE"""

        channel = f"user_events:{tenant_id}:{user_id}"
        await self.pubsub.subscribe(channel)

        return self.pubsub

    async def track_sse_connection(
        self,
        connection_id: str,
        user_id: UUID,
        tenant_id: UUID
    ):
        """Track SSE connection for this node"""

        connection_state = SSEConnectionState(
            connection_id=connection_id,
            user_id=user_id,
            tenant_id=tenant_id,
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            node_id=self.node_id
        )

        # Store connection state
        await self.redis.setex(
            f"sse_connection:{connection_id}",
            3600,  # 1 hour
            connection_state.model_dump_json()
        )

        # Track connections per user
        await self.redis.sadd(f"user_connections:{tenant_id}:{user_id}", connection_id)
        await self.redis.expire(f"user_connections:{tenant_id}:{user_id}", 3600)

    async def remove_sse_connection(self, connection_id: str):
        """Remove SSE connection tracking"""

        connection_data = await self.redis.get(f"sse_connection:{connection_id}")
        if connection_data:
            connection = SSEConnectionState.model_validate_json(connection_data)

            # Remove from user connections
            await self.redis.srem(
                f"user_connections:{connection.tenant_id}:{connection.user_id}",
                connection_id
            )

        await self.redis.delete(f"sse_connection:{connection_id}")
```

### FastAPI Integration with Session Management
```python
# middleware/session_middleware.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer(auto_error=False)

async def get_current_session(request: Request) -> Optional[UserSessionState]:
    """Extract and validate user session"""

    # Try to get session from cookie first
    session_id = request.cookies.get("session_id")

    if not session_id:
        # Try Authorization header
        credentials = await security(request)
        if credentials:
            try:
                payload = jwt.decode(
                    credentials.credentials,
                    settings.JWT_SECRET,
                    algorithms=["HS256"]
                )
                session_id = payload.get("session_id")
            except jwt.InvalidTokenError:
                pass

    if not session_id:
        return None

    session_service = SessionService()
    session = await session_service.get_user_session(session_id)

    if session:
        # Update last activity
        await session_service.update_user_session(
            session_id,
            {"last_activity": datetime.utcnow()}
        )

    return session

async def get_current_user_id(session: UserSessionState = Depends(get_current_session)) -> UUID:
    """Get current user ID from session"""
    if not session:
        raise HTTPException(401, "Authentication required")
    return session.user_id

async def get_current_tenant(session: UserSessionState = Depends(get_current_session)) -> UUID:
    """Get current tenant ID from session"""
    if not session:
        raise HTTPException(401, "Authentication required")
    return session.tenant_id

# SSE endpoint with multi-node support
@app.get("/events/{tenant_id}/{user_id}")
async def stream_user_events(
    tenant_id: UUID,
    user_id: UUID,
    request: Request,
    session: UserSessionState = Depends(get_current_session)
):
    """Server-Sent Events endpoint with multi-node support"""

    if session.tenant_id != tenant_id or session.user_id != user_id:
        raise HTTPException(403, "Access denied")

    async def event_generator():
        connection_id = str(uuid.uuid4())
        event_service = EventService()

        try:
            # Track this SSE connection
            await event_service.track_sse_connection(connection_id, user_id, tenant_id)

            # Subscribe to user events
            pubsub = await event_service.subscribe_to_user_events(tenant_id, user_id)

            last_event_id = "0"

            while True:
                if await request.is_disconnected():
                    break

                # Get any pending events from stream
                events = await event_service.get_user_events_since(
                    tenant_id, user_id, last_event_id
                )

                for event in events:
                    yield f"event: {event['event_type']}\n"
                    yield f"data: {json.dumps(event['data'])}\n"
                    yield f"id: {event['id']}\n\n"
                    last_event_id = event['id']

                # Listen for real-time events via pub/sub
                try:
                    message = await asyncio.wait_for(pubsub.get_message(), timeout=30)
                    if message and message['type'] == 'message':
                        event_data = json.loads(message['data'])
                        yield f"event: {event_data['event_type']}\n"
                        yield f"data: {json.dumps(event_data['data'])}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"event: heartbeat\n"
                    yield f"data: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"

        finally:
            await event_service.remove_sse_connection(connection_id)
            await pubsub.unsubscribe()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Docker Compose Configuration for Multi-Node Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: requirements_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  app-node-1:
    build: .
    ports:
      - "8001:8000"
    environment:
      - REDIS_HOST=redis
      - DATABASE_URL=postgresql://postgres:postgres@postgres/requirements_db
      - NODE_ID=node-1
    depends_on:
      - redis
      - postgres

  app-node-2:
    build: .
    ports:
      - "8002:8000"
    environment:
      - REDIS_HOST=redis
      - DATABASE_URL=postgresql://postgres:postgres@postgres/requirements_db
      - NODE_ID=node-2
    depends_on:
      - redis
      - postgres

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app-node-1
      - app-node-2

volumes:
  redis_data:
  postgres_data:
```

This session management solution provides:
- **Stateless application nodes** - any node can handle any request
- **Persistent sessions** across server restarts and load balancing
- **Real-time event delivery** to users regardless of connected node
- **Automatic cleanup** of expired sessions and connections
- **Scalable architecture** that works with any number of application nodes
"""
Redis client configuration and connection management.
Provides async Redis setup for sessions, caching, and pub/sub.
"""

from typing import Optional, Any, Dict, List
import json
import pickle
from datetime import datetime, timedelta

import structlog
import redis.asyncio as redis
from redis.asyncio import Redis

from src.config import settings

logger = structlog.get_logger(__name__)

# Global Redis clients
redis_client: Optional[Redis] = None
redis_session_client: Optional[Redis] = None
redis_cache_client: Optional[Redis] = None
redis_celery_client: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize Redis connections for different purposes."""
    global redis_client, redis_session_client, redis_cache_client, redis_celery_client

    logger.info("Initializing Redis connections", url=settings.redis_url.split("@")[0] + "@***")

    try:
        # Main Redis client
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={},
            retry_on_timeout=True,
        )

        # Session management (DB 0)
        session_url = settings.redis_url.replace("/0", f"/{settings.redis_session_db}")
        redis_session_client = redis.from_url(
            session_url,
            decode_responses=True,
            health_check_interval=30,
        )

        # Cache (DB 1)
        cache_url = settings.redis_url.replace("/0", f"/{settings.redis_cache_db}")
        redis_cache_client = redis.from_url(
            cache_url,
            decode_responses=True,
            health_check_interval=30,
        )

        # Celery (DB 2)
        celery_url = settings.redis_url.replace("/0", f"/{settings.redis_celery_db}")
        redis_celery_client = redis.from_url(
            celery_url,
            decode_responses=True,
            health_check_interval=30,
        )

        # Test connections
        await redis_client.ping()
        await redis_session_client.ping()
        await redis_cache_client.ping()
        await redis_celery_client.ping()

        logger.info("Redis connections initialized successfully")

    except Exception as e:
        logger.error("Failed to initialize Redis connections", error=str(e))
        raise


async def close_redis() -> None:
    """Close all Redis connections."""
    logger.info("Closing Redis connections")

    clients = [redis_client, redis_session_client, redis_cache_client, redis_celery_client]
    for client in clients:
        if client:
            await client.close()

    logger.info("Redis connections closed")


class RedisManager:
    """Redis operations manager with helper methods."""

    @staticmethod
    async def get_session_client() -> Redis:
        """Get Redis client for session management."""
        if not redis_session_client:
            raise RuntimeError("Redis session client not initialized")
        return redis_session_client

    @staticmethod
    async def get_cache_client() -> Redis:
        """Get Redis client for caching."""
        if not redis_cache_client:
            raise RuntimeError("Redis cache client not initialized")
        return redis_cache_client

    @staticmethod
    async def get_main_client() -> Redis:
        """Get main Redis client."""
        if not redis_client:
            raise RuntimeError("Redis client not initialized")
        return redis_client

    @staticmethod
    async def set_json(client: Redis, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set JSON value in Redis with optional TTL."""
        try:
            json_value = json.dumps(value, default=str)
            if ttl:
                return await client.setex(key, ttl, json_value)
            else:
                return await client.set(key, json_value)
        except Exception as e:
            logger.error("Failed to set JSON value in Redis", key=key, error=str(e))
            return False

    @staticmethod
    async def get_json(client: Redis, key: str, default: Any = None) -> Any:
        """Get JSON value from Redis."""
        try:
            value = await client.get(key)
            if value:
                return json.loads(value)
            return default
        except Exception as e:
            logger.error("Failed to get JSON value from Redis", key=key, error=str(e))
            return default

    @staticmethod
    async def set_pickle(client: Redis, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set pickled value in Redis with optional TTL."""
        try:
            pickled_value = pickle.dumps(value)
            if ttl:
                return await client.setex(key, ttl, pickled_value)
            else:
                return await client.set(key, pickled_value)
        except Exception as e:
            logger.error("Failed to set pickled value in Redis", key=key, error=str(e))
            return False

    @staticmethod
    async def get_pickle(client: Redis, key: str, default: Any = None) -> Any:
        """Get pickled value from Redis."""
        try:
            value = await client.get(key)
            if value:
                return pickle.loads(value)
            return default
        except Exception as e:
            logger.error("Failed to get pickled value from Redis", key=key, error=str(e))
            return default

    @staticmethod
    async def delete_pattern(client: Redis, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Failed to delete keys by pattern", pattern=pattern, error=str(e))
            return 0

    @staticmethod
    async def get_ttl(client: Redis, key: str) -> int:
        """Get TTL for a key."""
        try:
            return await client.ttl(key)
        except Exception as e:
            logger.error("Failed to get TTL", key=key, error=str(e))
            return -1

    @staticmethod
    async def extend_ttl(client: Redis, key: str, ttl: int) -> bool:
        """Extend TTL for an existing key."""
        try:
            return await client.expire(key, ttl)
        except Exception as e:
            logger.error("Failed to extend TTL", key=key, error=str(e))
            return False


class SessionManager:
    """Session management using Redis."""

    @staticmethod
    async def create_session(
        user_id: str,
        tenant_id: str,
        session_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> str:
        """Create a new session."""
        session_id = f"session:{user_id}:{datetime.utcnow().timestamp()}"
        ttl = ttl or (settings.session_expire_hours * 3600)

        session_info = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            **session_data
        }

        client = await RedisManager.get_session_client()
        success = await RedisManager.set_json(client, session_id, session_info, ttl)

        if success:
            # Add to user's session list
            await client.sadd(f"user_sessions:{user_id}", session_id)
            await client.expire(f"user_sessions:{user_id}", ttl)

        return session_id if success else None

    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        client = await RedisManager.get_session_client()
        session_data = await RedisManager.get_json(client, session_id)

        if session_data:
            # Update last accessed
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            await RedisManager.set_json(
                client,
                session_id,
                session_data,
                settings.session_expire_hours * 3600
            )

        return session_data

    @staticmethod
    async def update_session(session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data."""
        client = await RedisManager.get_session_client()
        session_data = await RedisManager.get_json(client, session_id)

        if not session_data:
            return False

        session_data.update(updates)
        session_data["last_accessed"] = datetime.utcnow().isoformat()

        return await RedisManager.set_json(
            client,
            session_id,
            session_data,
            settings.session_expire_hours * 3600
        )

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """Delete a session."""
        client = await RedisManager.get_session_client()
        session_data = await RedisManager.get_json(client, session_id)

        if session_data:
            user_id = session_data.get("user_id")
            if user_id:
                await client.srem(f"user_sessions:{user_id}", session_id)

        return await client.delete(session_id) > 0

    @staticmethod
    async def get_user_sessions(user_id: str) -> List[str]:
        """Get all sessions for a user."""
        client = await RedisManager.get_session_client()
        return await client.smembers(f"user_sessions:{user_id}")


class CacheManager:
    """Cache management using Redis."""

    @staticmethod
    async def set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value."""
        client = await RedisManager.get_cache_client()
        return await RedisManager.set_json(client, f"cache:{key}", value, ttl)

    @staticmethod
    async def get(key: str, default: Any = None) -> Any:
        """Get cached value."""
        client = await RedisManager.get_cache_client()
        return await RedisManager.get_json(client, f"cache:{key}", default)

    @staticmethod
    async def delete(key: str) -> bool:
        """Delete cached value."""
        client = await RedisManager.get_cache_client()
        return await client.delete(f"cache:{key}") > 0

    @staticmethod
    async def clear_pattern(pattern: str) -> int:
        """Clear all cached values matching pattern."""
        client = await RedisManager.get_cache_client()
        return await RedisManager.delete_pattern(client, f"cache:{pattern}")


# Simplified Redis client for service layers
class RedisClient:
    """Simplified Redis client wrapper for service layers."""

    def __init__(self):
        self._client = None

    async def _get_client(self) -> Redis:
        """Get Redis client instance."""
        if not self._client:
            self._client = await RedisManager.get_main_client()
        return self._client

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in Redis."""
        client = await self._get_client()
        return await RedisManager.set_json(client, key, value, ttl)

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from Redis."""
        client = await self._get_client()
        return await RedisManager.get_json(client, key, default)

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        client = await self._get_client()
        return await client.delete(key) > 0

    async def setex(self, key: str, ttl: int, value: Any) -> bool:
        """Set a value with expiration time."""
        client = await self._get_client()
        return await RedisManager.set_json(client, key, value, ttl)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        client = await self._get_client()
        return await RedisManager.delete_pattern(client, pattern)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = await self._get_client()
        return await client.exists(key) > 0

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        client = await self._get_client()
        return await client.expire(key, ttl)

    async def ttl(self, key: str) -> int:
        """Get TTL for a key."""
        client = await self._get_client()
        return await client.ttl(key)


# Helper functions for dependency injection
async def get_redis_client() -> Redis:
    """FastAPI dependency to get main Redis client."""
    return await RedisManager.get_main_client()


async def get_cache_manager() -> CacheManager:
    """FastAPI dependency to get cache manager."""
    return CacheManager()


async def get_session_manager() -> SessionManager:
    """FastAPI dependency to get session manager."""
    return SessionManager()
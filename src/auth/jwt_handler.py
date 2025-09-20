"""
JWT token management for authentication and authorization.
Handles token creation, validation, and refresh functionality.
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from ..config import get_settings
from ..shared.exceptions import AuthenticationError, ValidationError


class JWTHandler:
    """JWT token creation and validation handler."""

    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Use secret key from settings or generate one
        self.secret_key = self.settings.secret_key
        self.algorithm = "HS256"

        # Token expiration times
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def create_access_token(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        email: str,
        role: str,
        permissions: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "tenant_id": str(tenant_id),
            "email": email,
            "role": role,
            "permissions": permissions or {},
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new JWT refresh token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError:
            raise AuthenticationError("Invalid token")

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify an access token and return payload."""
        payload = self.verify_token(token)

        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")

        return payload

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify a refresh token and return payload."""
        payload = self.verify_token(token)

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        return payload

    def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Extract user information from access token."""
        payload = self.verify_access_token(token)

        return {
            "user_id": uuid.UUID(payload["sub"]),
            "tenant_id": uuid.UUID(payload["tenant_id"]),
            "email": payload["email"],
            "role": payload["role"],
            "permissions": payload.get("permissions", {})
        }

    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token."""
        payload = self.verify_refresh_token(refresh_token)

        # Note: In a real implementation, you'd fetch current user data from DB
        # For now, we'll use the basic info from the refresh token
        return self.create_access_token(
            user_id=uuid.UUID(payload["sub"]),
            tenant_id=uuid.UUID(payload["tenant_id"]),
            email="",  # Would fetch from DB
            role="",   # Would fetch from DB
            permissions={}  # Would fetch from DB
        )

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def generate_reset_token(self, user_id: uuid.UUID, expires_hours: int = 1) -> str:
        """Generate a password reset token."""
        expire = datetime.utcnow() + timedelta(hours=expires_hours)

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "password_reset",
            "jti": str(uuid.uuid4())
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_reset_token(self, token: str) -> uuid.UUID:
        """Verify password reset token and return user ID."""
        payload = self.verify_token(token)

        if payload.get("type") != "password_reset":
            raise AuthenticationError("Invalid token type")

        return uuid.UUID(payload["sub"])

    def generate_invitation_token(
        self,
        email: str,
        tenant_id: uuid.UUID,
        role: str,
        expires_days: int = 7
    ) -> str:
        """Generate an invitation token for user signup."""
        expire = datetime.utcnow() + timedelta(days=expires_days)

        payload = {
            "email": email,
            "tenant_id": str(tenant_id),
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "invitation",
            "jti": str(uuid.uuid4())
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_invitation_token(self, token: str) -> Dict[str, Any]:
        """Verify invitation token and return invitation data."""
        payload = self.verify_token(token)

        if payload.get("type") != "invitation":
            raise AuthenticationError("Invalid token type")

        return {
            "email": payload["email"],
            "tenant_id": uuid.UUID(payload["tenant_id"]),
            "role": payload["role"],
            "jti": payload["jti"]
        }

    def create_api_key(self, user_id: uuid.UUID, tenant_id: uuid.UUID, name: str) -> str:
        """Create a long-lived API key for programmatic access."""
        # API keys don't expire but can be revoked
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "name": name,
            "iat": datetime.utcnow(),
            "type": "api_key",
            "jti": str(uuid.uuid4())
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_api_key(self, token: str) -> Dict[str, Any]:
        """Verify API key token."""
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={"verify_exp": False}  # API keys don't expire
        )

        if payload.get("type") != "api_key":
            raise AuthenticationError("Invalid token type")

        return {
            "user_id": uuid.UUID(payload["sub"]),
            "tenant_id": uuid.UUID(payload["tenant_id"]),
            "name": payload["name"],
            "jti": payload["jti"]
        }

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)

    def get_token_claims(self, token: str) -> Dict[str, Any]:
        """Get token claims without verification (for debugging)."""
        try:
            # Decode without verification to inspect claims
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
        except Exception:
            return {}


# Global JWT handler instance
jwt_handler = JWTHandler()
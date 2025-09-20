"""
Configuration management for the Requirements Generator application.
Supports multiple environments with proper validation.
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic import validator, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with environment-specific settings."""

    # Application
    app_name: str = "Requirements Generator"
    version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/requirements_db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_session_db: int = Field(default=0, env="REDIS_SESSION_DB")
    redis_cache_db: int = Field(default=1, env="REDIS_CACHE_DB")
    redis_celery_db: int = Field(default=2, env="REDIS_CELERY_DB")

    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    jwt_secret: str = Field(default="jwt-secret-key-change-in-production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")

    # AI Integration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_timeout: int = Field(default=30, env="OPENAI_TIMEOUT")

    # Azure OpenAI (fallback)
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment: str = Field(default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT")

    # Embeddings
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1536, env="EMBEDDING_DIMENSIONS")

    # Background Tasks
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")

    # Session Management
    session_expire_hours: int = Field(default=8, env="SESSION_EXPIRE_HOURS")
    conversation_expire_hours: int = Field(default=4, env="CONVERSATION_EXPIRE_HOURS")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    ai_rate_limit_per_hour: int = Field(default=100, env="AI_RATE_LIMIT_PER_HOUR")

    # File Storage
    upload_max_size: int = Field(default=10 * 1024 * 1024, env="UPLOAD_MAX_SIZE")  # 10MB
    allowed_extensions: List[str] = Field(
        default=[".md", ".txt", ".json", ".yaml", ".yml"],
        env="ALLOWED_EXTENSIONS"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )

    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    # Multi-tenant settings
    default_tenant_features: List[str] = Field(
        default=["ai_assistant", "requirements_management", "basic_collaboration"],
        env="DEFAULT_TENANT_FEATURES"
    )
    max_tenants_per_user: int = Field(default=3, env="MAX_TENANTS_PER_USER")

    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "testing", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("cors_methods", pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @validator("cors_headers", pre=True)
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v

    @validator("allowed_extensions", pre=True)
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @validator("default_tenant_features", pre=True)
    def parse_default_tenant_features(cls, v):
        if isinstance(v, str):
            return [feature.strip() for feature in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development-specific settings."""
    debug: bool = True
    reload: bool = True
    database_echo: bool = True
    log_level: str = "DEBUG"


class TestingSettings(Settings):
    """Testing-specific settings."""
    environment: str = "testing"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/requirements_test"
    redis_url: str = "redis://localhost:6379/15"  # Use different Redis DB for tests
    debug: bool = True
    log_level: str = "WARNING"


class ProductionSettings(Settings):
    """Production-specific settings."""
    debug: bool = False
    reload: bool = False
    database_echo: bool = False
    log_level: str = "INFO"
    bcrypt_rounds: int = 14


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance based on environment."""
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "development":
        return DevelopmentSettings()
    elif environment == "testing":
        return TestingSettings()
    elif environment == "production":
        return ProductionSettings()
    else:
        return Settings()


# Global settings instance
settings = get_settings()
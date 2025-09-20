"""
Development configuration with mock services.
"""

import os
from pydantic import Field
from src.config import Settings

class DevelopmentSettings(Settings):
    """Development settings with mock services enabled."""

    # Additional development-specific fields
    mock_openai: bool = Field(default=True, env="MOCK_OPENAI")

    class Config:
        env_file = ".env.dev"
        env_file_encoding = "utf-8"

    @property
    def use_mock_openai(self) -> bool:
        """Check if we should use mock OpenAI service."""
        return self.mock_openai


# Create development settings with overrides
dev_settings = DevelopmentSettings(
    debug=True,
    openai_api_key="mock-key-for-development",
    openai_model="gpt-4",
    mock_openai=True,
    database_url="sqlite+aiosqlite:///./dev_requirements.db",
    redis_url="redis://localhost:6379/0"  # Will be ignored if Redis not available
)
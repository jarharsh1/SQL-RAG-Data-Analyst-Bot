"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.models.schemas import AppConfig, DatabaseConfig, LLMConfig, SafetyConfig, SQLOperation


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.0
    embedding_model: str = "text-embedding-3-small"

    # Database Configuration
    database_url: str
    database_type: str = "postgresql"
    database_query_timeout: int = 30
    database_pool_size: int = 5

    # Safety Configuration
    max_result_rows: int = 10000
    max_query_timeout_seconds: int = 30
    allowed_tables: str = ""  # Comma-separated
    blocked_columns: str = ""  # Comma-separated

    # Vector Store
    chroma_persist_dir: str = "./data/vector_store"
    chroma_collection_name: str = "data_dictionary"

    # Audit Logging
    audit_log_path: str = "./data/audit_logs"
    audit_log_enabled: bool = True

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # Feature Flags
    enable_agentic_tools: bool = False
    enable_result_caching: bool = False
    enable_query_optimization: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_allowed_tables(self) -> List[str]:
        """Parse comma-separated allowed tables."""
        if not self.allowed_tables:
            return []
        return [t.strip() for t in self.allowed_tables.split(",") if t.strip()]

    def get_blocked_columns(self) -> List[str]:
        """Parse comma-separated blocked columns."""
        if not self.blocked_columns:
            # Default sensitive columns
            return [
                "ssn",
                "social_security_number",
                "credit_card",
                "credit_card_number",
                "password",
                "api_key",
                "secret",
                "token",
            ]
        return [c.strip() for c in self.blocked_columns.split(",") if c.strip()]

    def to_app_config(self) -> AppConfig:
        """Convert to AppConfig schema."""
        return AppConfig(
            environment=self.app_env,
            log_level=self.log_level,
            audit_log_enabled=self.audit_log_enabled,
            audit_log_path=self.audit_log_path,
            enable_agentic_tools=self.enable_agentic_tools,
            safety=SafetyConfig(
                max_result_rows=self.max_result_rows,
                max_query_timeout_seconds=self.max_query_timeout_seconds,
                allowed_tables=self.get_allowed_tables(),
                blocked_columns=self.get_blocked_columns(),
                allowed_operations=[SQLOperation.SELECT],
            ),
            database=DatabaseConfig(
                url=self.database_url,
                type=self.database_type,
                query_timeout=self.database_query_timeout,
                pool_size=self.database_pool_size,
            ),
            llm=LLMConfig(
                provider=self.llm_provider,
                model=self.llm_model,
                temperature=self.llm_temperature,
            ),
        )

    def validate_required_keys(self) -> None:
        """Validate that required API keys are present."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate_required_keys()
    return settings


def get_app_config() -> AppConfig:
    """Get application configuration."""
    return get_settings().to_app_config()

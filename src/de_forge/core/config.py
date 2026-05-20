"""Application configuration using Pydantic settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: str = Field(default="development", description="Environment name")

    # Database
    database_url: str = Field(
        default="sqlite:///./de_forge.db",
        description="Database connection URL",
    )

    # OpenAI-compatible API
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://shopapikey.com/v1",
        description="OpenAI-compatible base URL",
    )
    openai_model: str = Field(
        default="cx/gpt-5.5",
        description="Model identifier for all agents",
    )

    # Server
    port: int = Field(default=8000, description="Server port")
    host: str = Field(default="0.0.0.0", description="Server host")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")

    # Agent configuration
    max_static_refinement_iterations: int = Field(
        default=3,
        description="Maximum static refinement iterations",
    )
    max_dynamic_refinement_iterations: int = Field(
        default=2,
        description="Maximum dynamic refinement iterations",
    )

    # Security
    secret_key: str = Field(
        default="change_this_in_production",
        description="Secret key for signing",
    )


settings = Settings()

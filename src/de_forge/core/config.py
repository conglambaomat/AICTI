"""Application configuration using Pydantic settings."""

from collections.abc import Mapping
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from de_forge.core.constants import PROFILE_THRESHOLDS


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
    database_echo: bool = Field(default=False, description="Enable SQLAlchemy SQL echo logging")
    database_pool_pre_ping: bool = Field(
        default=True,
        description="Enable SQLAlchemy pool pre-ping health checks",
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
    enable_dev_seed_routes: bool = Field(
        default=False,
        description="Mount development-only seed routes when explicitly enabled.",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level")

    # Agent configuration
    profile: Literal["strict", "balanced", "exploratory"] = Field(
        default="balanced",
        description="Profile for KPI thresholds and budgets",
    )
    max_static_refinement_iterations: int = Field(
        default=3,
        description="Maximum static refinement iterations",
    )
    max_dynamic_refinement_iterations: int = Field(
        default=2,
        description="Maximum dynamic refinement iterations",
    )

    @property
    def profile_thresholds(self) -> Mapping[str, float | int]:
        """Return KPI thresholds and budgets for the active profile."""
        return PROFILE_THRESHOLDS[self.profile]

    @model_validator(mode="after")
    def validate_profile_threshold_mapping(self) -> "Settings":
        """Ensure configured profile exists in the threshold registry."""
        if self.profile not in PROFILE_THRESHOLDS:
            raise ValueError(f"Unsupported profile: {self.profile}")
        return self

    # Security
    secret_key: str = Field(
        default="change_this_in_production",
        description="Secret key for signing",
    )


settings = Settings()

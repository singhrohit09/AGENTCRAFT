"""
RakshaGrid Configuration & Environment Settings
Defines strongly-typed, validated configuration variables for
disaster intelligence operations, database connectivity, and telemetry.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RakshaGridSettings(BaseSettings):
    """Configuration settings for RakshaGrid disaster intelligence platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Identifiers
    RAKSHAGRID_APP_NAME: str = "RakshaGrid"
    RAKSHAGRID_SUBTITLE: str = "Disaster Intelligence and Response"
    RAKSHAGRID_VERSION: str = "1.0.0-phase1"
    RAKSHAGRID_ENV: str = Field(default="development", description="Execution environment")
    RAKSHAGRID_DEMO_MODE: bool = Field(
        default=True,
        description="Whether fictional emergency demo data is served for Phase 1 verification.",
    )

    # Operational Parameters
    RAKSHAGRID_DEFCON_LEVEL: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Disaster Alert Severity Level (1=Catastrophic/Defcon 1 to 5=Routine/Standby)",
    )
    RAKSHAGRID_ALERT_THRESHOLD: str = Field(
        default="MODERATE",
        description="Minimum severity threshold for auto-escalating broadcast alerts.",
    )

    # PostgreSQL Database Credentials
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL database host")
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL database port")
    POSTGRES_DB: str = Field(default="rakshagrid", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="", description="PostgreSQL user password")
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Full connection URI. If omitted, built dynamically from discrete POSTGRES_* fields.",
    )

    # DB Connection Pool Config
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_TIMEOUT_SECONDS: int = Field(default=5, ge=1, le=60)

    @field_validator("RAKSHAGRID_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        normalized = v.lower().strip()
        if normalized not in allowed:
            raise ValueError(f"RAKSHAGRID_ENV must be one of {allowed}, got: {v}")
        return normalized

    @field_validator("RAKSHAGRID_ALERT_THRESHOLD")
    @classmethod
    def validate_threshold(cls, v: str) -> str:
        allowed = {"MINOR", "MODERATE", "SEVERE", "CRITICAL", "EXTREME"}
        normalized = v.upper().strip()
        if normalized not in allowed:
            raise ValueError(f"RAKSHAGRID_ALERT_THRESHOLD must be one of {allowed}, got: {v}")
        return normalized

    @property
    def effective_database_url(self) -> str:
        """Returns the PostgreSQL connection URL formatted for psycopg3/SQLAlchemy."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Using psycopg driver format for PostgreSQL
        auth = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@" if self.POSTGRES_PASSWORD else f"{self.POSTGRES_USER}@"
        return f"postgresql+psycopg://{auth}{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def is_database_configured(self) -> bool:
        """Indicates whether non-default credentials or explicit DATABASE_URL are set."""
        return bool(self.DATABASE_URL or self.POSTGRES_PASSWORD)


# Global singleton instance
rakshagrid_settings = RakshaGridSettings()

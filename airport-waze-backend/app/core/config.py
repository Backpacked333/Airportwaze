"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "AirportWaze API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENV: str = "production"  # development, staging, production

    # API
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://user:password@localhost:5432/airportwaze"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # 5 minutes
    PREDICTION_CACHE_TTL: int = 600  # 10 minutes

    # Security
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_RANDOM_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Monte Carlo Simulation
    SIMULATION_RUNS: int = 10000
    SIMULATION_RUNS_FAST: int = 5000  # For quick calculations

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # External APIs
    TSA_API_URL: str = "https://www.tsa.gov/data/apcp.xml"
    TSA_API_TIMEOUT: int = 10

    # Crowdsourced Reports
    MAX_REPORTS_IN_MEMORY: int = 10000
    REPORTS_CLEANUP_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for getting settings."""
    return settings

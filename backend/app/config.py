"""Application Configuration using Pydantic Settings."""

from typing import List, Union, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PROJECT_NAME: str = "Career Intelligence API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server Binding & URLs
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    WORKERS: int = 4
    API_BASE_URL: str = "http://localhost:8000"
    
    # Security & Cryptography
    SECRET_KEY: str = Field(
        default="insecure-dev-secret-key-change-in-production-min-32-chars",
        description="Cryptographic secret key for session, JWT, and payload integrity."
    )
    OPTIONAL_AI_API_KEY: Optional[str] = Field(
        default=None,
        description="Optional AI provider API key for extended offline/online services."
    )
    
    # API Documentation Controls
    ENABLE_DOCS: bool = False
    
    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Database
    DATABASE_URL: str = "sqlite:///./career_intelligence.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DEBUG", mode="after")
    @classmethod
    def validate_debug_mode(cls, v: bool, info) -> bool:
        """Enforces that debug mode is strictly disabled in production."""
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and v is True:
            raise ValueError(
                "DEBUG mode must be disabled (DEBUG=false) when ENVIRONMENT=production."
            )
        return v

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Enforces that production secrets are supplied from environment variables and meet minimum entropy."""
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if "insecure" in v.lower() or "dev-secret" in v.lower() or len(v) < 32:
                raise ValueError(
                    "Production deployment requires a cryptographically strong SECRET_KEY "
                    "(at least 32 characters) provided via environment variables."
                )
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def validate_cors_origins(cls, v: Union[str, List[str]], info) -> Union[str, List[str]]:
        """Restricts wildcard CORS in production environments."""
        env = info.data.get("ENVIRONMENT", "development")
        raw_list = [origin.strip() for origin in v.split(",")] if isinstance(v, str) else v
        if env == "production" and ("*" in raw_list):
            raise ValueError(
                "Wildcard CORS ('*') is strictly forbidden in production. "
                "Specify explicit origin domains (e.g. CORS_ORIGINS=https://app.yourdomain.com)."
            )
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return ["http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()

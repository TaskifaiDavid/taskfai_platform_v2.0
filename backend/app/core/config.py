"""
Application Configuration
Uses Pydantic v2 Settings Management
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "TaskifAI Analytics Platform"
    app_version: str = "2.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Database
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    database_url: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # SendGrid
    sendgrid_api_key: str
    sendgrid_from_email: str
    sendgrid_from_name: str = "TaskifAI"

    # File Upload
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list[str] = [".xlsx", ".xls", ".csv"]
    upload_dir: str = "/tmp/uploads"

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
    ]

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

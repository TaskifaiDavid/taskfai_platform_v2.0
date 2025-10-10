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

    # Database (Dual Purpose: Tenant Registry + Demo Tenant Data)
    # NOTE: In production, tenant registry would be a separate database
    # For development, we use the same Supabase project for both:
    # 1. Tenant registry tables (tenants, user_tenants, tenant_configs)
    # 2. Demo tenant application data (users, products, orders, etc.)
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    database_url: Optional[str] = None

    # Tenant Registry (uses same Supabase project in development)
    # In production: Set these to a separate Supabase project URL/keys
    @property
    def tenant_registry_url(self) -> str:
        """Tenant registry database URL (defaults to main supabase_url in dev)"""
        return self.supabase_url

    @property
    def tenant_registry_anon_key(self) -> str:
        """Tenant registry anon key (defaults to main supabase_anon_key in dev)"""
        return self.supabase_anon_key

    @property
    def tenant_registry_service_key(self) -> str:
        """Tenant registry service key (defaults to main supabase_service_key in dev)"""
        return self.supabase_service_key

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI (Optional - AI chat disabled if not configured)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # SendGrid (Optional - email notifications disabled if not configured)
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""
    sendgrid_from_name: str = "TaskifAI"

    # File Upload
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions_str: str = ".xlsx,.xls,.csv"  # Comma-separated for env vars
    upload_dir: str = "/tmp/uploads"

    # CORS (stored as comma-separated string for DigitalOcean env vars)
    # Pydantic v2 tries to JSON parse list[str], but env vars are plain comma-separated strings
    allowed_origins_str: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5173"

    @property
    def allowed_extensions(self) -> list[str]:
        """Parse comma-separated extensions into list"""
        return [ext.strip() for ext in self.allowed_extensions_str.split(",")]

    @property
    def allowed_origins(self) -> list[str]:
        """Parse comma-separated origins into list"""
        return [origin.strip() for origin in self.allowed_origins_str.split(",")]

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

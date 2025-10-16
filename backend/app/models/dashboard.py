"""Dashboard configuration models"""

from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class DashboardBase(BaseModel):
    """Base dashboard configuration model"""
    dashboard_name: str = Field(min_length=1, max_length=255)
    dashboard_type: str = Field(
        pattern="^(looker|tableau|powerbi|metabase|custom)$"
    )
    dashboard_url: str = Field(min_length=1)
    authentication_method: str = Field(
        default="none",
        pattern="^(none|bearer_token|api_key|oauth)$"
    )
    authentication_config: Optional[dict[str, Any]] = None
    permissions: Optional[list[str]] = None
    is_active: bool = False

    @validator('dashboard_name')
    def validate_name(cls, v):
        """Validate dashboard name"""
        if not v or not v.strip():
            raise ValueError("Dashboard name cannot be empty")
        return v.strip()

    @validator('dashboard_url')
    def validate_url(cls, v):
        """Validate dashboard URL format"""
        if not v or not v.strip():
            raise ValueError("Dashboard URL cannot be empty")
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Dashboard URL must start with http:// or https://")
        if v.startswith('http://localhost') or 'localhost' in v or '127.0.0.1' in v:
            raise ValueError("Localhost URLs are not allowed in production")
        return v

    @validator('authentication_config')
    def validate_auth_config(cls, v, values):
        """Validate authentication config based on method"""
        auth_method = values.get('authentication_method')
        if auth_method and auth_method != 'none' and not v:
            raise ValueError(f"Authentication config required for method: {auth_method}")
        return v


class DashboardCreate(DashboardBase):
    """Model for creating dashboard"""
    user_id: str


class DashboardUpdate(BaseModel):
    """Model for updating dashboard"""
    dashboard_name: Optional[str] = Field(None, min_length=1, max_length=255)
    dashboard_type: Optional[str] = Field(
        None,
        pattern="^(looker|tableau|powerbi|metabase|custom)$"
    )
    dashboard_url: Optional[str] = None
    authentication_method: Optional[str] = Field(
        None,
        pattern="^(none|bearer_token|api_key|oauth)$"
    )
    authentication_config: Optional[dict[str, Any]] = None
    permissions: Optional[list[str]] = None
    is_active: Optional[bool] = None

    @validator('dashboard_url')
    def validate_url(cls, v):
        """Validate dashboard URL format if provided"""
        if v:
            v = v.strip()
            if not v.startswith(('http://', 'https://')):
                raise ValueError("Dashboard URL must start with http:// or https://")
            if v.startswith('http://localhost') or 'localhost' in v or '127.0.0.1' in v:
                raise ValueError("Localhost URLs are not allowed in production")
        return v


class DashboardInDB(DashboardBase):
    """Dashboard as stored in database"""
    config_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(DashboardBase):
    """Dashboard response"""
    config_id: str
    created_at: datetime
    updated_at: datetime
    is_primary: bool = False  # Computed field based on is_active

    model_config = {"from_attributes": True}


class DashboardList(BaseModel):
    """List of dashboards"""
    dashboards: list[DashboardResponse]
    total: int
    primary_dashboard: Optional[DashboardResponse] = None


class DashboardEmbedRequest(BaseModel):
    """Request for dashboard embedding"""
    config_id: str
    auto_refresh: bool = False
    refresh_interval_seconds: Optional[int] = Field(None, ge=30, le=3600)


class DashboardEmbedResponse(BaseModel):
    """Response for dashboard embedding"""
    embed_url: str
    dashboard_name: str
    dashboard_type: str
    requires_auth: bool
    sandbox_attributes: list[str] = Field(
        default_factory=lambda: [
            "allow-scripts",
            "allow-same-origin",
            "allow-forms"
        ]
    )


class DashboardAccessLog(BaseModel):
    """Dashboard access log entry"""
    config_id: str
    user_id: str
    accessed_at: datetime
    duration_seconds: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None

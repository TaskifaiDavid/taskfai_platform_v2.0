"""
Pydantic models for tenant management
"""

from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field, validator
import re


class TenantBase(BaseModel):
    """Base tenant model with common fields"""
    company_name: str = Field(..., min_length=1, max_length=255)
    subdomain: str = Field(..., min_length=3, max_length=50)

    @validator('subdomain')
    def validate_subdomain(cls, v):
        """Validate subdomain format"""
        # Alphanumeric and hyphens only
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Subdomain must contain only lowercase letters, numbers, and hyphens')

        # Cannot start/end with hyphen
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Subdomain cannot start or end with a hyphen')

        # Reserved subdomains
        reserved = ['www', 'api', 'admin', 'app', 'staging', 'demo', 'test', 'dev']
        if v in reserved:
            raise ValueError(f'Subdomain "{v}" is reserved')

        return v


class TenantCreate(TenantBase):
    """Model for creating a new tenant"""
    database_url: str = Field(..., description="Supabase project URL")
    database_credentials: 'TenantCredentials' = Field(..., description="Database credentials")
    admin_email: str = Field(..., description="Initial admin user email")
    admin_name: Optional[str] = Field(None, description="Initial admin user name")
    metadata: Optional[Dict] = None

    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Database URL must be a valid Supabase URL (https://)')
        return v


class TenantUpdate(BaseModel):
    """Model for updating tenant"""
    company_name: Optional[str] = None
    database_url: Optional[str] = None
    database_credentials: Optional['TenantCredentials'] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None


class TenantInDB(TenantBase):
    """Tenant model as stored in database"""
    tenant_id: str
    database_url: str  # Encrypted in DB
    database_credentials: str  # Encrypted JSON: {anon_key, service_key}
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    metadata: Optional[Dict] = None

    class Config:
        from_attributes = True

    @validator('is_active')
    def check_active_status(cls, v, values):
        """Ensure suspended tenants are not active"""
        if 'suspended_at' in values and values['suspended_at'] is not None:
            if v is True:
                raise ValueError('Cannot set is_active=True when tenant is suspended')
        return v


class Tenant(TenantInDB):
    """Public tenant model (without sensitive data)"""
    access_url: str

    @classmethod
    def from_db(cls, db_tenant: TenantInDB) -> "Tenant":
        """Create public tenant from DB model"""
        data = db_tenant.dict()
        # Remove sensitive fields
        data.pop('database_credentials', None)
        # Add computed fields
        data['access_url'] = f"https://{db_tenant.subdomain}.taskifai.com"
        return cls(**data)


class TenantResponse(BaseModel):
    """Public tenant response model (no sensitive data)"""
    tenant_id: UUID = Field(..., description="Tenant unique ID")
    subdomain: str = Field(..., description="Tenant subdomain")
    company_name: str = Field(..., description="Company name")
    database_url: str = Field(..., description="Database URL")
    is_active: bool = Field(..., description="Whether tenant is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class TenantConfig(BaseModel):
    """Tenant-specific configuration"""
    tenant_id: str
    max_file_size_mb: int = 100
    allowed_vendors: Optional[list[str]] = None  # None = all vendors
    custom_branding: Optional[Dict] = None
    features_enabled: Dict[str, bool] = {
        "ai_chat": True,
        "dashboards": True,
        "email_reports": True,
        "api_access": False
    }


class SubdomainCheck(BaseModel):
    """Model for subdomain availability check"""
    subdomain: str
    available: bool
    reason: Optional[str] = None


class TenantCredentials(BaseModel):
    """Database credentials for tenant"""
    anon_key: str = Field(..., description="Supabase anon key")
    service_key: str = Field(..., description="Supabase service key")

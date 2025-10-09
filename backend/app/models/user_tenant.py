"""
UserTenant Pydantic Models

Defines data models for user-tenant mapping system:
- UserTenant: User-tenant association with role
- UserTenantCreate: Request model for adding user to tenant
- UserTenantUpdate: Request model for updating user role
- UserTenantResponse: Response model for user-tenant information
- UserTenantListResponse: List of users in a tenant
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class UserRole(str):
    """User role enum values"""
    MEMBER = "member"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserTenantBase(BaseModel):
    """Base user-tenant fields"""
    email: str = Field(..., description="User email address")
    role: str = Field(
        default=UserRole.MEMBER,
        description="User role in tenant (member, admin, super_admin)"
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is a valid enum value"""
        valid_roles = [UserRole.MEMBER, UserRole.ADMIN, UserRole.SUPER_ADMIN]
        if v not in valid_roles:
            raise ValueError(
                f'Role must be one of: {", ".join(valid_roles)}'
            )
        return v


class UserTenantCreate(UserTenantBase):
    """Request model for adding user to tenant"""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@acme.com",
            "role": "member"
        }
    })


class UserTenantUpdate(BaseModel):
    """Request model for updating user role in tenant"""
    role: str = Field(..., description="Updated user role")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is a valid enum value"""
        valid_roles = [UserRole.MEMBER, UserRole.ADMIN, UserRole.SUPER_ADMIN]
        if v not in valid_roles:
            raise ValueError(
                f'Role must be one of: {", ".join(valid_roles)}'
            )
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "role": "admin"
        }
    })


class UserTenantResponse(UserTenantBase):
    """Response model for user-tenant information"""
    id: UUID = Field(..., description="User-tenant mapping ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    created_at: datetime = Field(..., description="When user was added to tenant")
    updated_at: Optional[datetime] = Field(None, description="Last role update")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "email": "user@acme.com",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "member",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z"
            }
        }
    )


class UserTenantListResponse(BaseModel):
    """Response model for list of users in a tenant"""
    users: list[UserTenantResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users in tenant")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "users": [
                {
                    "id": "660e8400-e29b-41d4-a716-446655440001",
                    "email": "user@acme.com",
                    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                    "role": "member",
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T10:30:00Z"
                }
            ],
            "total": 1
        }
    })


class UserTenant(UserTenantBase):
    """Complete user-tenant model (internal use)"""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

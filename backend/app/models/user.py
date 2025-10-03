"""User models for authentication"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="analyst", pattern="^(analyst|admin)$")


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data response (no password)"""
    user_id: str
    email: str
    full_name: str
    role: str
    created_at: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    user_id: Optional[str] = None
    email: Optional[str] = None

"""Reseller models for B2B partner management"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ResellerBase(BaseModel):
    """Base reseller model"""
    name: str = Field(min_length=1, max_length=255)
    country: Optional[str] = Field(None, max_length=100)

    @validator('name')
    def validate_name(cls, v):
        """Validate reseller name"""
        if not v or not v.strip():
            raise ValueError("Reseller name cannot be empty")
        return v.strip()

    @validator('country')
    def validate_country(cls, v):
        """Validate and normalize country"""
        if v:
            return v.strip()
        return v


class ResellerCreate(ResellerBase):
    """Model for creating reseller"""
    pass


class ResellerUpdate(BaseModel):
    """Model for updating reseller"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    country: Optional[str] = Field(None, max_length=100)

    @validator('name')
    def validate_name(cls, v):
        """Validate reseller name"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Reseller name cannot be empty")
        return v.strip() if v else v


class ResellerInDB(ResellerBase):
    """Reseller as stored in database"""
    reseller_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResellerResponse(ResellerBase):
    """Reseller response"""
    reseller_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResellerList(BaseModel):
    """List of resellers with pagination"""
    resellers: list[ResellerResponse]
    total: int
    page: int = 1
    page_size: int = 50


class ResellerSearch(BaseModel):
    """Reseller search filters"""
    name: Optional[str] = None
    country: Optional[str] = None
    search_term: Optional[str] = None  # Full-text search


class ResellerWithStats(ResellerResponse):
    """Reseller with sales statistics"""
    total_sales_eur: float
    total_quantity: int
    total_orders: int
    last_order_date: Optional[datetime] = None

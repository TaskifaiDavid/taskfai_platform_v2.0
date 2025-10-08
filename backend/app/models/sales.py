"""Sales models for offline (B2B) and online (D2C) sales data"""

from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class OfflineSaleBase(BaseModel):
    """Base model for offline/wholesale sales (B2B)"""
    functional_name: str = Field(min_length=1, max_length=255)
    product_ean: Optional[str] = Field(None, min_length=13, max_length=13)
    reseller: str = Field(min_length=1, max_length=255)
    sales_eur: Decimal = Field(gt=0, decimal_places=2)
    quantity: int = Field(gt=0)
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)

    @validator('product_ean')
    def validate_ean(cls, v):
        """Validate EAN format if provided"""
        if v and not v.isdigit():
            raise ValueError("EAN must contain only digits")
        return v


class OfflineSaleCreate(OfflineSaleBase):
    """Model for creating offline sale"""
    user_id: str
    product_id: Optional[str] = None
    reseller_id: Optional[str] = None
    upload_batch_id: Optional[str] = None


class OfflineSaleInDB(OfflineSaleBase):
    """Offline sale as stored in database"""
    sale_id: str
    user_id: str
    product_id: Optional[str]
    reseller_id: Optional[str]
    upload_batch_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class OfflineSaleResponse(OfflineSaleBase):
    """Offline sale response"""
    sale_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OnlineSaleBase(BaseModel):
    """Base model for online/ecommerce sales (D2C)"""
    product_ean: Optional[str] = Field(None, min_length=13, max_length=13)
    functional_name: str = Field(min_length=1, max_length=255)
    product_name: Optional[str] = Field(None, max_length=255)
    sales_eur: Decimal = Field(gt=0, decimal_places=2)
    quantity: int = Field(gt=0)
    cost_of_goods: Optional[Decimal] = Field(None, decimal_places=2)
    stripe_fee: Optional[Decimal] = Field(None, decimal_places=2)
    order_date: date
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=255)
    utm_source: Optional[str] = Field(None, max_length=255)
    utm_medium: Optional[str] = Field(None, max_length=255)
    utm_campaign: Optional[str] = Field(None, max_length=255)
    device_type: Optional[str] = Field(None, pattern="^(mobile|desktop|tablet)$")
    reseller: str = Field(default="Online", max_length=255)

    @validator('product_ean')
    def validate_ean(cls, v):
        """Validate EAN format if provided"""
        if v and not v.isdigit():
            raise ValueError("EAN must contain only digits")
        return v


class OnlineSaleCreate(OnlineSaleBase):
    """Model for creating online sale"""
    user_id: str
    upload_batch_id: Optional[str] = None


class OnlineSaleInDB(OnlineSaleBase):
    """Online sale as stored in database"""
    order_id: str
    user_id: str
    upload_batch_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class OnlineSaleResponse(OnlineSaleBase):
    """Online sale response"""
    order_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SalesFilter(BaseModel):
    """Filter options for sales queries"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reseller: Optional[str] = None
    product_ean: Optional[str] = None
    functional_name: Optional[str] = None
    country: Optional[str] = None
    channel: Optional[str] = Field(None, pattern="^(online|offline|all)$")
    min_sales: Optional[Decimal] = None
    max_sales: Optional[Decimal] = None


class SalesSummary(BaseModel):
    """Aggregated sales summary"""
    total_sales_eur: Decimal
    total_quantity: int
    total_orders: int
    avg_order_value: Decimal
    period_start: Optional[date] = None
    period_end: Optional[date] = None

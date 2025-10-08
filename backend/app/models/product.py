"""Product models for sales data management"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ProductBase(BaseModel):
    """Base product model"""
    sku: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=255)
    product_ean: Optional[str] = Field(None, min_length=13, max_length=13)
    functional_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)

    @validator('product_ean')
    def validate_ean(cls, v):
        """Validate EAN format if provided"""
        if v and not v.isdigit():
            raise ValueError("EAN must contain only digits")
        if v and len(v) != 13:
            raise ValueError("EAN must be exactly 13 digits")
        return v

    @validator('sku')
    def validate_sku(cls, v):
        """Validate SKU format"""
        if not v or not v.strip():
            raise ValueError("SKU cannot be empty")
        return v.strip().upper()


class ProductCreate(ProductBase):
    """Model for creating product"""
    pass


class ProductUpdate(BaseModel):
    """Model for updating product"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    product_ean: Optional[str] = Field(None, min_length=13, max_length=13)
    functional_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)

    @validator('product_ean')
    def validate_ean(cls, v):
        """Validate EAN format if provided"""
        if v and not v.isdigit():
            raise ValueError("EAN must contain only digits")
        if v and len(v) != 13:
            raise ValueError("EAN must be exactly 13 digits")
        return v


class ProductInDB(ProductBase):
    """Product as stored in database"""
    product_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductResponse(ProductBase):
    """Product response"""
    product_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductList(BaseModel):
    """List of products with pagination"""
    products: list[ProductResponse]
    total: int
    page: int = 1
    page_size: int = 50


class ProductSearch(BaseModel):
    """Product search filters"""
    sku: Optional[str] = None
    product_name: Optional[str] = None
    product_ean: Optional[str] = None
    functional_name: Optional[str] = None
    category: Optional[str] = None
    search_term: Optional[str] = None  # Full-text search across all fields

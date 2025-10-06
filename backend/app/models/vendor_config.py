"""
Pydantic models for vendor configuration
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class FileFormat(BaseModel):
    """File format configuration"""
    type: str = Field(..., pattern="^(excel|csv)$")
    sheet_name: Optional[str] = None
    header_row: int = 0
    skip_rows: int = 0
    pivot_format: bool = False


class TransformationRules(BaseModel):
    """Data transformation rules"""
    currency_conversion: Optional[str] = None  # e.g., "PLN_to_EUR"
    date_format: str = "YYYY-MM-DD"
    ean_cleanup: bool = True
    price_rounding: int = 2


class ValidationRules(BaseModel):
    """Data validation rules"""
    ean_length: int = 13
    month_range: List[int] = [1, 12]
    year_range: List[int] = [2000, 2100]
    required_fields: List[str]
    nullable_fields: List[str] = []


class DetectionRules(BaseModel):
    """Vendor detection rules"""
    filename_keywords: List[str]
    sheet_names: List[str] = []
    required_columns: List[str]
    confidence_threshold: float = 0.7


class VendorConfigData(BaseModel):
    """Complete vendor configuration data"""
    vendor_name: str
    currency: str = "EUR"
    exchange_rate: float = 1.0
    file_format: FileFormat
    column_mapping: Dict[str, str]
    transformation_rules: TransformationRules = TransformationRules()
    validation_rules: ValidationRules
    detection_rules: DetectionRules
    metadata: Optional[Dict[str, Any]] = None

    @validator('column_mapping')
    def validate_required_mappings(cls, v):
        """Ensure required fields are mapped"""
        required = ['product_ean', 'quantity', 'month', 'year']
        missing = [f for f in required if f not in v]
        if missing:
            raise ValueError(f"Missing required column mappings: {missing}")
        return v


class VendorConfigCreate(BaseModel):
    """Model for creating vendor config"""
    vendor_name: str
    tenant_id: Optional[str] = None  # None for default configs
    config_data: VendorConfigData
    is_active: bool = True
    is_default: bool = False


class VendorConfigUpdate(BaseModel):
    """Model for updating vendor config"""
    config_data: Optional[VendorConfigData] = None
    is_active: Optional[bool] = None


class VendorConfigInDB(BaseModel):
    """Vendor config as stored in database"""
    config_id: str
    tenant_id: Optional[str]
    vendor_name: str
    config_data: Dict[str, Any]  # JSONB in database
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VendorConfig(BaseModel):
    """Public vendor configuration model"""
    config_id: str
    vendor_name: str
    config_data: VendorConfigData
    is_active: bool
    is_custom: bool  # True if tenant override, False if default
    source: str  # "tenant_override" or "system_default"

    @classmethod
    def from_db(cls, db_config: VendorConfigInDB, is_custom: bool = False) -> "VendorConfig":
        """Create public config from DB model"""
        return cls(
            config_id=db_config.config_id,
            vendor_name=db_config.vendor_name,
            config_data=VendorConfigData(**db_config.config_data),
            is_active=db_config.is_active,
            is_custom=is_custom,
            source="tenant_override" if is_custom else "system_default"
        )


class VendorConfigList(BaseModel):
    """List of vendor configurations"""
    configs: List[VendorConfig]
    total: int

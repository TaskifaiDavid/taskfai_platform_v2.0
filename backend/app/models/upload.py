"""Upload batch models for file processing tracking"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class UploadBatchBase(BaseModel):
    """Base upload batch model"""
    original_filename: str = Field(min_length=1, max_length=500)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    vendor_name: Optional[str] = Field(None, max_length=100)
    upload_mode: str = Field(pattern="^(append|replace)$")

    @validator('original_filename')
    def validate_filename(cls, v):
        """Validate filename"""
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()


class UploadBatchCreate(UploadBatchBase):
    """Model for creating upload batch"""
    uploader_user_id: str


class UploadBatchUpdate(BaseModel):
    """Model for updating upload batch"""
    processing_status: Optional[str] = Field(
        None,
        pattern="^(pending|processing|completed|failed)$"
    )
    rows_total: Optional[int] = Field(None, ge=0)
    rows_processed: Optional[int] = Field(None, ge=0)
    rows_failed: Optional[int] = Field(None, ge=0)
    total_sales_eur: Optional[Decimal] = Field(None, decimal_places=2)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None
    vendor_name: Optional[str] = Field(None, max_length=100)


class UploadBatchInDB(UploadBatchBase):
    """Upload batch as stored in database"""
    upload_batch_id: str
    uploader_user_id: str
    processing_status: str
    rows_total: Optional[int]
    rows_processed: Optional[int]
    rows_failed: Optional[int]
    total_sales_eur: Optional[Decimal]
    upload_timestamp: datetime
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_summary: Optional[str]

    model_config = {"from_attributes": True}


class UploadBatchResponse(BaseModel):
    """Upload batch response"""
    upload_batch_id: str
    original_filename: str
    file_size_bytes: Optional[int]
    vendor_name: Optional[str]
    upload_mode: str
    processing_status: str
    rows_total: Optional[int]
    rows_processed: Optional[int]
    rows_failed: Optional[int]
    total_sales_eur: Optional[Decimal]
    upload_timestamp: datetime
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_summary: Optional[str]
    processing_duration_seconds: Optional[float] = None

    model_config = {"from_attributes": True}

    @validator('processing_duration_seconds', always=True)
    def calculate_duration(cls, v, values):
        """Calculate processing duration if available"""
        if values.get('processing_started_at') and values.get('processing_completed_at'):
            delta = values['processing_completed_at'] - values['processing_started_at']
            return delta.total_seconds()
        return None


class UploadBatchList(BaseModel):
    """List of upload batches with pagination"""
    batches: list[UploadBatchResponse]
    total: int
    page: int = 1
    page_size: int = 50


class UploadBatchFilter(BaseModel):
    """Filter options for upload batches"""
    vendor_name: Optional[str] = None
    processing_status: Optional[str] = Field(
        None,
        pattern="^(pending|processing|completed|failed)$"
    )
    upload_mode: Optional[str] = Field(None, pattern="^(append|replace)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ErrorReportBase(BaseModel):
    """Base error report model"""
    upload_batch_id: str
    row_number_in_file: int = Field(ge=1)
    error_type: str = Field(min_length=1, max_length=100)
    error_message: str = Field(min_length=1)
    raw_data: Optional[dict] = None


class ErrorReportCreate(ErrorReportBase):
    """Model for creating error report"""
    pass


class ErrorReportInDB(ErrorReportBase):
    """Error report as stored in database"""
    error_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ErrorReportResponse(ErrorReportBase):
    """Error report response"""
    error_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ErrorReportList(BaseModel):
    """List of error reports"""
    errors: list[ErrorReportResponse]
    total: int

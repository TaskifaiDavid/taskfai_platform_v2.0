"""Email log models for notification tracking"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class EmailLogBase(BaseModel):
    """Base email log model"""
    email_type: str = Field(
        pattern="^(success|failure|scheduled_report)$"
    )
    recipient_email: EmailStr
    subject: str = Field(min_length=1)
    status: str = Field(
        default="pending",
        pattern="^(sent|failed|pending)$"
    )
    error_message: Optional[str] = None
    attachment_count: int = Field(default=0, ge=0)
    attachment_size: int = Field(default=0, ge=0)

    @validator('subject')
    def validate_subject(cls, v):
        """Validate subject is not empty"""
        if not v or not v.strip():
            raise ValueError("Subject cannot be empty")
        return v.strip()

    @validator('error_message')
    def validate_error_message(cls, v, values):
        """Ensure error message is provided when status is failed"""
        status = values.get('status')
        if status == 'failed' and not v:
            raise ValueError("Error message required when status is 'failed'")
        return v


class EmailLogCreate(EmailLogBase):
    """Model for creating email log"""
    user_id: Optional[str] = None


class EmailLogUpdate(BaseModel):
    """Model for updating email log"""
    status: Optional[str] = Field(
        None,
        pattern="^(sent|failed|pending)$"
    )
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None


class EmailLogInDB(EmailLogBase):
    """Email log as stored in database"""
    log_id: str
    user_id: Optional[str]
    sent_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailLogResponse(EmailLogBase):
    """Email log response"""
    log_id: str
    sent_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailLogList(BaseModel):
    """List of email logs with pagination"""
    logs: list[EmailLogResponse]
    total: int
    page: int = 1
    page_size: int = 50


class EmailLogFilter(BaseModel):
    """Filter options for email logs"""
    email_type: Optional[str] = Field(
        None,
        pattern="^(success|failure|scheduled_report)$"
    )
    status: Optional[str] = Field(
        None,
        pattern="^(sent|failed|pending)$"
    )
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    recipient_email: Optional[str] = None


class EmailTemplate(BaseModel):
    """Email template configuration"""
    template_name: str = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=500)
    html_content: str = Field(min_length=1)
    text_content: Optional[str] = None
    variables: list[str] = Field(default_factory=list)


class EmailSendRequest(BaseModel):
    """Request to send email"""
    recipient_email: EmailStr
    email_type: str = Field(
        pattern="^(success|failure|scheduled_report)$"
    )
    subject: str = Field(min_length=1, max_length=500)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    template_name: Optional[str] = None
    template_variables: Optional[dict] = None
    attachments: Optional[list[dict]] = None

    @validator('template_variables')
    def validate_template_vars(cls, v, values):
        """Ensure template variables provided when template specified"""
        template = values.get('template_name')
        if template and not v:
            raise ValueError("Template variables required when using template")
        return v


class EmailSendResponse(BaseModel):
    """Response after sending email"""
    log_id: str
    status: str
    sent_at: datetime
    error_message: Optional[str] = None


class EmailStats(BaseModel):
    """Email statistics"""
    total_sent: int
    total_failed: int
    total_pending: int
    success_rate: float = Field(ge=0.0, le=100.0)
    by_type: dict[str, int] = Field(default_factory=dict)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

"""
Pydantic models for Multi-Factor Authentication endpoints

Request and response models for TOTP 2FA enrollment, verification, and management.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MFAEnrollRequest(BaseModel):
    """Request to enroll in 2FA - requires password verification"""

    password: str = Field(
        ...,
        min_length=8,
        description="Current password for identity verification before MFA enrollment"
    )


class MFAEnrollResponse(BaseModel):
    """Response with QR code and backup codes for enrollment"""

    qr_code: str = Field(
        ...,
        description="Base64 data URI (data:image/png;base64,...) for QR code display"
    )
    secret: str = Field(
        ...,
        description="Base32 secret for manual entry into authenticator app"
    )
    backup_codes: List[str] = Field(
        ...,
        description="Single-use recovery codes (store securely)",
        min_length=10,
        max_length=10
    )
    message: str = Field(
        default="Scan QR code with your authenticator app and verify to complete enrollment",
        description="Instructions for next step"
    )


class MFAVerifyRequest(BaseModel):
    """Request to verify TOTP code"""

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit code from authenticator app"
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate code is 6 digits"""
        if not v.isdigit():
            raise ValueError("Code must be numeric")
        if len(v) != 6:
            raise ValueError("Code must be exactly 6 digits")
        return v


class MFADisableRequest(BaseModel):
    """Request to disable 2FA - requires password + current TOTP code"""

    password: str = Field(
        ...,
        min_length=8,
        description="Current password for identity verification"
    )
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Current 6-digit TOTP code for verification"
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate code is 6 digits"""
        if not v.isdigit():
            raise ValueError("Code must be numeric")
        if len(v) != 6:
            raise ValueError("Code must be exactly 6 digits")
        return v


class MFAStatusResponse(BaseModel):
    """Current MFA enrollment status for authenticated user"""

    mfa_enabled: bool = Field(
        ...,
        description="Whether 2FA is currently enabled"
    )
    enrolled_at: Optional[datetime] = Field(
        None,
        description="Timestamp when MFA was enabled (null if not enabled)"
    )
    backup_codes_remaining: int = Field(
        default=0,
        description="Number of unused backup codes available",
        ge=0
    )


class MFALoginVerifyRequest(BaseModel):
    """Request to complete MFA-protected login"""

    temp_token: str = Field(
        ...,
        description="Temporary token from initial login response"
    )
    mfa_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code from authenticator app"
    )

    @field_validator("mfa_code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate code is 6 digits"""
        if not v.isdigit():
            raise ValueError("Code must be numeric")
        if len(v) != 6:
            raise ValueError("Code must be exactly 6 digits")
        return v


class MFABackupCodeRequest(BaseModel):
    """Request to use backup recovery code for login"""

    temp_token: str = Field(
        ...,
        description="Temporary token from initial login response"
    )
    backup_code: str = Field(
        ...,
        description="One of the backup recovery codes from enrollment"
    )


class MFARegenerateBackupCodesRequest(BaseModel):
    """Request to regenerate backup codes"""

    password: str = Field(
        ...,
        min_length=8,
        description="Current password for identity verification"
    )
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Current TOTP code for verification"
    )


class MFARegenerateBackupCodesResponse(BaseModel):
    """Response with new backup codes"""

    backup_codes: List[str] = Field(
        ...,
        description="New single-use recovery codes (store securely)",
        min_length=10,
        max_length=10
    )
    message: str = Field(
        default="Backup codes regenerated. Old codes are now invalid.",
        description="Warning about old codes being invalidated"
    )

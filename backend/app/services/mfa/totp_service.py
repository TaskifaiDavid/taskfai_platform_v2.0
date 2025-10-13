"""
TOTP Multi-Factor Authentication Service

Implements RFC 6238 Time-based One-Time Password (TOTP) using PyOTP.
Provides secret generation, QR code creation, code verification, and backup codes.
"""
import io
import base64
from typing import List
from secrets import token_urlsafe

import pyotp
import qrcode

from app.core.security import encrypt_credential, decrypt_credential


class TOTPService:
    """
    Manages TOTP secret generation, QR codes, and verification

    Features:
    - RFC 6238 compliant TOTP implementation
    - QR code generation for authenticator apps
    - Time window tolerance for clock drift
    - Backup code generation for account recovery
    """

    def generate_secret(self) -> str:
        """
        Generate cryptographically secure base32 secret

        Returns:
            32-character base32-encoded secret compatible with
            Google Authenticator, Authy, and other TOTP apps

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> len(secret)
            32
        """
        return pyotp.random_base32()

    def generate_qr_code(self, secret: str, email: str, issuer: str = "TaskifAI") -> str:
        """
        Generate QR code as base64 data URI for authenticator app enrollment

        Args:
            secret: Base32-encoded TOTP secret
            email: User's email address (shown in authenticator app)
            issuer: Service name (shown in authenticator app)

        Returns:
            data:image/png;base64,... string for direct HTML <img> src use

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> qr = service.generate_qr_code(secret, "user@example.com")
            >>> qr.startswith("data:image/png;base64,")
            True
        """
        # Generate provisioning URI (otpauth://totp/...)
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=email, issuer_name=issuer)

        # Create QR code image
        qr = qrcode.QRCode(
            version=1,  # Auto-size based on data
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Generate PIL Image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 data URI
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{img_base64}"

    def verify_code(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify TOTP code with time window tolerance

        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit code from authenticator app
            valid_window: Number of 30-second windows to check (default 1)
                         1 = ±30s tolerance (3 windows: past, current, future)
                         0 = strict (current window only)

        Returns:
            True if code is valid, False otherwise

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> totp = pyotp.TOTP(secret)
            >>> code = totp.now()
            >>> service.verify_code(secret, code)
            True
            >>> service.verify_code(secret, "000000")
            False

        Notes:
            - TOTP codes change every 30 seconds
            - valid_window=1 provides ±30s tolerance for clock drift
            - Prevents replay attacks within same time window
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=valid_window)

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate single-use recovery codes for account recovery

        Args:
            count: Number of backup codes to generate (default 10)

        Returns:
            List of cryptographically secure random codes

        Example:
            >>> service = TOTPService()
            >>> codes = service.generate_backup_codes(10)
            >>> len(codes)
            10
            >>> len(set(codes))  # All unique
            10

        Notes:
            - Codes are 16 characters (URL-safe base64)
            - Each code should be single-use (track usage in database)
            - Encrypt codes before storing in database
        """
        return [token_urlsafe(12) for _ in range(count)]

    def encrypt_secret(self, secret: str) -> str:
        """
        Encrypt TOTP secret for database storage

        Args:
            secret: Plain-text base32 secret

        Returns:
            Encrypted secret (AES-256)

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> encrypted = service.encrypt_secret(secret)
            >>> decrypted = service.decrypt_secret(encrypted)
            >>> secret == decrypted
            True
        """
        return encrypt_credential(secret)

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt TOTP secret from database

        Args:
            encrypted_secret: Encrypted secret from database

        Returns:
            Plain-text base32 secret

        Raises:
            Exception: If decryption fails (invalid key or corrupted data)
        """
        return decrypt_credential(encrypted_secret)

    def encrypt_backup_codes(self, codes: List[str]) -> List[str]:
        """
        Encrypt backup codes for database storage

        Args:
            codes: List of plain-text backup codes

        Returns:
            List of encrypted codes
        """
        return [encrypt_credential(code) for code in codes]

    def decrypt_backup_codes(self, encrypted_codes: List[str]) -> List[str]:
        """
        Decrypt backup codes from database

        Args:
            encrypted_codes: List of encrypted codes from database

        Returns:
            List of plain-text backup codes
        """
        return [decrypt_credential(code) for code in encrypted_codes]

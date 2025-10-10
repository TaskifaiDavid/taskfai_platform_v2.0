"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import base64
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    tenant_id: Optional[str] = None,
    subdomain: Optional[str] = None,
    role: Optional[str] = None,
    expires_minutes: Optional[int] = None,
    expires_delta: Optional[timedelta] = None,
    add_jti: bool = False
) -> str:
    """
    Create JWT access token with optional tenant claims

    Args:
        data: Payload data to encode in token (user_id, email)
        tenant_id: Optional tenant ID for multi-tenant routing
        subdomain: Optional tenant subdomain for validation
        role: User role (member, admin, super_admin) for authorization
        expires_minutes: Optional expiration time in minutes (overrides expires_delta)
        expires_delta: Optional custom expiration timedelta
        add_jti: If True, add JWT ID for one-time use tracking (default False)

    Returns:
        Encoded JWT token string with tenant claims (if provided)

    Example:
        >>> # Full token with tenant
        >>> token = create_access_token(
        ...     {"sub": "user_id", "email": "user@example.com"},
        ...     tenant_id="tenant_123",
        ...     subdomain="customer1",
        ...     role="admin"
        ... )
        >>> # Temporary token without tenant (multi-tenant user)
        >>> temp_token = create_access_token(
        ...     {"sub": "user_id", "email": "user@example.com", "temp": True},
        ...     expires_minutes=5,
        ...     add_jti=True  # Enable one-time use tracking
        ... )
    """
    to_encode = data.copy()

    # Add tenant claims for multi-tenant security (if provided)
    if tenant_id:
        to_encode["tenant_id"] = tenant_id
    if subdomain:
        to_encode["subdomain"] = subdomain

    # Add role claim if provided
    if role:
        to_encode["role"] = role

    # Add JWT ID for one-time use tracking (if requested)
    if add_jti:
        to_encode["jti"] = str(uuid.uuid4())

    # Add issued-at timestamp (useful for debugging and token freshness checks)
    to_encode["iat"] = datetime.now(timezone.utc)

    # Determine expiration time
    if expires_minutes:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    elif expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


# Credential Encryption
# =====================

def _get_encryption_key() -> bytes:
    """
    Derive encryption key from secret key using PBKDF2

    Returns:
        32-byte encryption key for AES-256
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'taskifai_tenant_credentials',  # Static salt for deterministic key
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(settings.secret_key.encode()))


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt sensitive credential using AES-256

    Args:
        plaintext: Credential to encrypt (database URL, API key, etc.)

    Returns:
        Base64-encoded encrypted credential

    Example:
        >>> encrypted = encrypt_credential("postgresql://user:pass@host/db")
        >>> decrypted = decrypt_credential(encrypted)
    """
    if not plaintext:
        return ""

    key = _get_encryption_key()
    fernet = Fernet(key)
    encrypted_bytes = fernet.encrypt(plaintext.encode())
    return encrypted_bytes.decode()


def decrypt_credential(encrypted: str) -> str:
    """
    Decrypt credential encrypted with encrypt_credential

    Args:
        encrypted: Base64-encoded encrypted credential

    Returns:
        Decrypted plaintext credential

    Raises:
        Exception: If decryption fails (invalid key or corrupted data)
    """
    if not encrypted:
        return ""

    key = _get_encryption_key()
    fernet = Fernet(key)
    decrypted_bytes = fernet.decrypt(encrypted.encode())
    return decrypted_bytes.decode()


# Aliases for backwards compatibility
encrypt_data = encrypt_credential
decrypt_data = decrypt_credential

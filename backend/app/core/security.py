"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import base64

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
    tenant_id: str,
    subdomain: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with tenant claims

    Args:
        data: Payload data to encode in token (user_id, email, role)
        tenant_id: Tenant ID for multi-tenant routing
        subdomain: Tenant subdomain for validation
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string with tenant claims

    Example:
        >>> token = create_access_token(
        ...     {"sub": "user_id", "email": "user@example.com"},
        ...     tenant_id="tenant_123",
        ...     subdomain="customer1"
        ... )
    """
    to_encode = data.copy()

    # Add tenant claims for multi-tenant security
    to_encode.update({
        "tenant_id": tenant_id,
        "subdomain": subdomain,
    })

    if expires_delta:
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

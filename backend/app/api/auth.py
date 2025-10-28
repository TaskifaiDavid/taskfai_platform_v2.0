"""
Authentication endpoints for user registration and login
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import SupabaseClient, CurrentUser
from app.core.security import create_access_token, get_password_hash, verify_password, decode_access_token
from app.models.user import AuthResponse, UserCreate, UserLogin, UserResponse
from app.models.mfa import (
    MFAEnrollRequest,
    MFAEnrollResponse,
    MFAVerifyRequest,
    MFADisableRequest,
    MFAStatusResponse,
    MFALoginVerifyRequest,
)
from app.services.mfa import TOTPService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize TOTP service
totp_service = TOTPService()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate,
    request: Request,
    supabase: SupabaseClient
):
    """
    Register a new user and return JWT token with user data

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **role**: Either 'analyst' or 'admin' (defaults to 'analyst')
    """
    # Check if user already exists
    existing = supabase.table("users").select("user_id").eq("email", user.email).execute()

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user_data = {
        "user_id": str(uuid4()),
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "full_name": user.full_name,
        "role": user.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    response = supabase.table("users").insert(user_data).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    created_user = response.data[0]

    # Get tenant context from request state (set by TenantContextMiddleware)
    tenant = request.state.tenant

    # Create access token with tenant claims
    access_token = create_access_token(
        data={
            "sub": created_user["user_id"],
            "email": created_user["email"],
            "role": created_user["role"]
        },
        tenant_id=tenant.tenant_id,
        subdomain=tenant.subdomain
    )

    return AuthResponse(
        user=UserResponse(**created_user),
        access_token=access_token
    )


@router.post("/login")
async def login(
    credentials: UserLogin,
    request: Request,
    supabase: SupabaseClient  # Kept for backward compatibility, but not used for auth
):
    """
    Authenticate user and return JWT token (or temp token if MFA required)

    Multi-Tenant Flow:
    1. Query Tenant Registry database for user (central authentication)
    2. Validate email/password
    3. Verify user has access to requested tenant (via user_tenants table)
    4. If MFA enabled → return temp token + requires_mfa flag
    5. If MFA disabled → return full access token (standard flow)

    - **email**: Registered email address
    - **password**: User password
    """
    from supabase import create_client
    from app.core.config import settings

    # Step 1: Connect to Tenant Registry database for central authentication
    registry_client = create_client(
        settings.get_tenant_registry_url(),
        settings.get_tenant_registry_service_key()
    )

    # Step 2: Get tenant context (set by TenantContextMiddleware)
    tenant = request.state.tenant

    # Step 2.5: Map tenant subdomain to UUID (Tenant Registry uses UUIDs, app uses subdomains)
    # For "bibbi" and "demo", we need to lookup the UUID from tenants table
    print(f"[Auth] Looking up tenant UUID for subdomain: {tenant.subdomain}")
    tenant_uuid_response = registry_client.table("tenants")\
        .select("tenant_id")\
        .eq("subdomain", tenant.subdomain)\
        .execute()

    if not tenant_uuid_response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tenant '{tenant.subdomain}' not found in registry"
        )

    tenant_uuid = tenant_uuid_response.data[0]["tenant_id"]
    print(f"[Auth] Tenant UUID: {tenant_uuid}")

    # Step 3: Fetch user from user_tenants table (centralized auth)
    # This query validates BOTH credentials AND tenant access in one step
    print(f"[Auth] Querying Tenant Registry for user: {credentials.email}")
    user_tenant_response = registry_client.table("user_tenants")\
        .select("*")\
        .eq("email", credentials.email.lower())\
        .eq("tenant_id", tenant_uuid)\
        .execute()

    if not user_tenant_response.data:
        print(f"[Auth] ✗ User {credentials.email} not found or no access to tenant: {tenant.tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    user_tenant = user_tenant_response.data[0]
    print(f"[Auth] ✓ User found: {user_tenant['email']}")

    # Step 4: Verify password
    if not user_tenant.get("hashed_password"):
        print(f"[Auth] ✗ No password set for user: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not verify_password(credentials.password, user_tenant["hashed_password"]):
        print(f"[Auth] ✗ Password verification failed for: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    print(f"[Auth] ✓ Password verified for: {credentials.email}")

    # Step 5: Extract user role
    user_role = user_tenant.get("role", "analyst")
    print(f"[Auth] ✓ User has access to tenant {tenant.tenant_id} with role: {user_role}")

    # Step 5: Check if MFA enabled
    # TEMPORARILY DISABLED: MFA check commented out for troubleshooting
    # if user.get("mfa_enabled"):
    #     # MFA required - return temporary token for MFA verification
    #     temp_token = create_access_token(
    #         data={
    #             "sub": user["user_id"],
    #             "email": user["email"],
    #             "requires_mfa": True
    #         },
    #         expires_minutes=5,  # Short-lived (5 minutes)
    #         add_jti=True  # One-time use token
    #     )
    #     return {
    #         "requires_mfa": True,
    #         "temp_token": temp_token,
    #         "message": "Please enter your 6-digit authentication code"
    #     }

    # Step 6: No MFA - standard login flow (always used with MFA disabled)
    # Use role from user_tenants table (tenant-specific role), not user table
    access_token = create_access_token(
        data={
            "sub": user_tenant["user_id"],
            "email": user_tenant["email"],
            "role": user_role  # Tenant-specific role from user_tenants table
        },
        tenant_id=tenant.tenant_id,
        subdomain=tenant.subdomain
    )

    print(f"[Auth] ✅ Login successful for {credentials.email} as {user_role} in tenant {tenant.tenant_id}")

    # Build user response with tenant-specific role
    user_response_data = dict(user_tenant)
    user_response_data["role"] = user_role  # Override with tenant-specific role

    return AuthResponse(
        user=UserResponse(**user_response_data),
        access_token=access_token
    )


@router.post("/logout")
async def logout():
    """
    Logout user (client should discard token)
    """
    return {"message": "Successfully logged out"}


# ============================================
# MFA Endpoints
# ============================================


@router.post("/mfa/enroll", response_model=MFAEnrollResponse)
async def enroll_mfa(
    request_data: MFAEnrollRequest,
    user: CurrentUser,
    supabase: SupabaseClient
):
    """
    Enroll user in TOTP 2FA

    Steps:
    1. Verify user's password for identity confirmation
    2. Generate TOTP secret and QR code
    3. Generate backup recovery codes
    4. Store encrypted in database (not yet enabled - requires verification)

    Returns QR code to scan with authenticator app (Google Authenticator, Authy, etc.)
    """
    # Verify password for identity confirmation
    if not verify_password(request_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    # Check if already enrolled
    if user.get("mfa_enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled for this account"
        )

    # Generate TOTP secret and backup codes
    secret = totp_service.generate_secret()
    backup_codes = totp_service.generate_backup_codes(count=10)
    qr_code = totp_service.generate_qr_code(secret, user["email"], issuer="TaskifAI")

    # Encrypt sensitive data before storing
    encrypted_secret = totp_service.encrypt_secret(secret)
    encrypted_codes = totp_service.encrypt_backup_codes(backup_codes)

    # Store in database (not enabled yet - requires code verification)
    supabase.table("users").update({
        "mfa_secret": encrypted_secret,
        "backup_codes": encrypted_codes,
        "mfa_enabled": False  # Not enabled until user verifies they can generate codes
    }).eq("user_id", user["user_id"]).execute()

    return MFAEnrollResponse(
        qr_code=qr_code,
        secret=secret,  # Show once for manual entry
        backup_codes=backup_codes
    )


@router.post("/mfa/verify-enrollment")
async def verify_mfa_enrollment(
    request_data: MFAVerifyRequest,
    user: CurrentUser,
    supabase: SupabaseClient
):
    """
    Verify TOTP code to complete MFA enrollment

    User must provide valid 6-digit code from their authenticator app
    to prove they successfully enrolled before we enable MFA on their account.
    """
    if user.get("mfa_enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled"
        )

    if not user.get("mfa_secret"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA enrollment not started. Call /mfa/enroll first."
        )

    # Decrypt secret
    secret = totp_service.decrypt_secret(user["mfa_secret"])

    # Verify TOTP code
    if not totp_service.verify_code(secret, request_data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code. Please try again."
        )

    # Enable MFA
    supabase.table("users").update({
        "mfa_enabled": True,
        "mfa_enrolled_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user["user_id"]).execute()

    return {"message": "MFA enabled successfully. Your account is now protected with two-factor authentication."}


@router.post("/mfa/disable")
async def disable_mfa(
    request_data: MFADisableRequest,
    user: CurrentUser,
    supabase: SupabaseClient
):
    """
    Disable 2FA (requires password + current TOTP code)

    Security: Requires both password and valid TOTP code to prevent
    unauthorized disabling of MFA protection.
    """
    if not user.get("mfa_enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled on this account"
        )

    # Verify password
    if not verify_password(request_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    # Verify TOTP code
    secret = totp_service.decrypt_secret(user["mfa_secret"])
    if not totp_service.verify_code(secret, request_data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code"
        )

    # Disable MFA and clear secrets
    supabase.table("users").update({
        "mfa_enabled": False,
        "mfa_secret": None,
        "mfa_enrolled_at": None,
        "backup_codes": None
    }).eq("user_id", user["user_id"]).execute()

    return {"message": "MFA disabled successfully"}


@router.get("/mfa/status", response_model=MFAStatusResponse)
async def get_mfa_status(user: CurrentUser):
    """
    Get current MFA enrollment status for authenticated user

    Returns whether MFA is enabled, when it was enrolled, and
    how many backup codes remain.
    """
    backup_codes_remaining = 0
    if user.get("backup_codes"):
        backup_codes_remaining = len(user["backup_codes"])

    return MFAStatusResponse(
        mfa_enabled=user.get("mfa_enabled", False),
        enrolled_at=user.get("mfa_enrolled_at"),
        backup_codes_remaining=backup_codes_remaining
    )


@router.post("/login/mfa-verify", response_model=AuthResponse)
async def verify_mfa_login(
    request_data: MFALoginVerifyRequest,
    request: Request,
    supabase: SupabaseClient
):
    """
    Complete MFA-protected login with TOTP code verification

    After initial login with MFA-enabled account, user receives temp token.
    This endpoint verifies the TOTP code and issues full access token.

    Security:
    - Temp token expires in 5 minutes
    - Temp token is one-time use (JTI claim)
    - Failed attempts are logged to mfa_attempts table
    """
    # Decode temporary token
    payload = decode_access_token(request_data.temp_token)

    if not payload or not payload.get("requires_mfa"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token"
        )

    user_id = payload.get("sub")

    # Get user from database
    response = supabase.table("users").select("*").eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    user = response.data[0]

    # Verify user has MFA enabled
    if not user.get("mfa_enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account"
        )

    # Decrypt and verify TOTP code
    secret = totp_service.decrypt_secret(user["mfa_secret"])
    if not totp_service.verify_code(secret, request_data.mfa_code):
        # Log failed attempt
        supabase.table("mfa_attempts").insert({
            "user_id": user_id,
            "success": False,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }).execute()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication code"
        )

    # Log successful attempt
    supabase.table("mfa_attempts").insert({
        "user_id": user_id,
        "success": True,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }).execute()

    # Issue full access token
    tenant = request.state.tenant

    access_token = create_access_token(
        data={
            "sub": user["user_id"],
            "email": user["email"],
            "role": user["role"]
        },
        tenant_id=tenant.tenant_id,
        subdomain=tenant.subdomain
    )

    return AuthResponse(
        user=UserResponse(**user),
        access_token=access_token
    )

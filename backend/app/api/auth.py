"""
Authentication endpoints for user registration and login
"""

from datetime import datetime, timezone
from typing import Annotated, Union
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import create_client

from app.core.dependencies import SupabaseClient
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.config import settings
from app.core.rate_limiter import get_rate_limiter
from app.models.user import AuthResponse, Token, UserCreate, UserLogin, UserResponse
from app.models.tenant import (
    TenantDiscoveryRequest,
    TenantDiscoverySingleResponse,
    TenantDiscoveryMultiResponse,
    LoginAndDiscoverRequest,
    LoginAndDiscoverSingleResponse,
    LoginAndDiscoverMultiResponse
)
from app.services.tenant_discovery import TenantDiscoveryService
from app.services.tenant_auth_discovery import TenantAuthDiscoveryService

router = APIRouter(prefix="/auth", tags=["Authentication"])


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


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    supabase: SupabaseClient
):
    """
    Authenticate user and return JWT token with user data

    - **email**: Registered email address
    - **password**: User password
    """
    # Fetch user by email
    response = supabase.table("users").select("*").eq("email", credentials.email).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    user = response.data[0]

    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Get tenant context from request state (set by TenantContextMiddleware)
    tenant = request.state.tenant

    # Create access token with tenant claims
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


@router.post("/logout")
async def logout():
    """
    Logout user (client should discard token)
    """
    return {"message": "Successfully logged out"}


@router.post(
    "/discover-tenant",
    response_model=Union[TenantDiscoverySingleResponse, TenantDiscoveryMultiResponse],
    status_code=status.HTTP_200_OK
)
async def discover_tenant(
    discovery_request: TenantDiscoveryRequest,
    request: Request
):
    """
    Discover tenant(s) for user email address

    Used by central login portal to route user to correct tenant subdomain.

    **Rate Limit**: 10 requests per minute per IP (prevents email enumeration)

    **Single Tenant User:**
    - Returns redirect URL to tenant subdomain login page

    **Multi-Tenant User:**
    - Returns list of tenants for user selection

    **No Tenant:**
    - Returns 404 if email not found in any tenant

    - **email**: User email address
    """
    # Rate limiting: 10 requests per minute per IP
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()

    is_limited, retry_after = rate_limiter.is_rate_limited(
        key=f"discover:{client_ip}",
        max_requests=10,
        window_seconds=60
    )

    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    try:
        # Create tenant registry client
        registry_client = create_client(
            settings.tenant_registry_url,
            settings.tenant_registry_anon_key
        )

        # Initialize discovery service
        discovery_service = TenantDiscoveryService(registry_client)

        # Discover tenant(s)
        result = discovery_service.discover_tenant(discovery_request)

        return result

    except ValueError as e:
        # Email not found in any tenant
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover tenant: {str(e)}"
        )


@router.post(
    "/login-and-discover",
    response_model=Union[LoginAndDiscoverSingleResponse, LoginAndDiscoverMultiResponse],
    status_code=status.HTTP_200_OK
)
async def login_and_discover(
    login_request: LoginAndDiscoverRequest,
    request: Request
):
    """
    Combined authentication + tenant discovery endpoint (Flow B)

    Authenticates user credentials and discovers associated tenants in single request.
    Used by central login portal at app.taskifai.com.

    **Rate Limit**: 10 requests per minute per IP (prevents brute force attacks)

    **Single Tenant User:**
    - Returns JWT token + redirect URL to tenant dashboard
    - User is logged in and redirected immediately

    **Multi-Tenant User:**
    - Returns temporary token + list of tenants for selection
    - User selects tenant, then exchanges temp token for real token

    **Authentication Failure:**
    - Returns 401 if credentials invalid or user not found

    - **email**: User email address
    - **password**: User password
    """
    # Rate limiting: 10 requests per minute per IP
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()

    is_limited, retry_after = rate_limiter.is_rate_limited(
        key=f"login:{client_ip}",
        max_requests=10,
        window_seconds=60
    )

    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    try:
        # Create tenant registry client
        registry_client = create_client(
            settings.tenant_registry_url,
            settings.tenant_registry_anon_key
        )

        # Initialize auth discovery service
        auth_discovery_service = TenantAuthDiscoveryService(registry_client)

        # Authenticate and discover tenant(s)
        result = auth_discovery_service.login_and_discover(login_request)

        return result

    except ValueError as e:
        # Authentication failure or no tenants found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

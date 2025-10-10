"""
Tenant Discovery endpoints for multi-tenant authentication

Handles tenant discovery, combined login+discovery, and token exchange
for routing users to the correct tenant subdomain.

Used by central login portal at app.taskifai.com.
"""

from typing import Annotated, Union

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client

from app.core.config import settings
from app.core.rate_limit_dependency import rate_limit
from app.core.security import create_access_token, decode_access_token
from app.core.token_blacklist import get_token_blacklist
from app.models.tenant import (
    TenantDiscoveryRequest,
    TenantDiscoverySingleResponse,
    TenantDiscoveryMultiResponse,
    LoginAndDiscoverRequest,
    LoginAndDiscoverSingleResponse,
    LoginAndDiscoverMultiResponse,
    ExchangeTokenRequest,
    ExchangeTokenResponse
)
from app.services.tenant_discovery import TenantDiscoveryService
from app.services.tenant_auth_discovery import TenantAuthDiscoveryService

router = APIRouter(prefix="/auth", tags=["Tenant Discovery"])


@router.post(
    "/discover-tenant",
    response_model=Union[TenantDiscoverySingleResponse, TenantDiscoveryMultiResponse],
    status_code=status.HTTP_200_OK
)
async def discover_tenant(
    discovery_request: TenantDiscoveryRequest,
    _: Annotated[None, Depends(rate_limit("discover", max_requests=10, window_seconds=60))]
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
    _: Annotated[None, Depends(rate_limit("login", max_requests=10, window_seconds=60))]
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


@router.post(
    "/exchange-token",
    response_model=ExchangeTokenResponse,
    status_code=status.HTTP_200_OK
)
async def exchange_token(
    exchange_request: ExchangeTokenRequest,
    _: Annotated[None, Depends(rate_limit("exchange", max_requests=10, window_seconds=60))]
):
    """
    Exchange temporary token for tenant-scoped token

    Used when multi-tenant user selects a specific tenant after login.
    The temporary token from /login-and-discover is exchanged for a
    real JWT token scoped to the selected tenant.

    **Security Features:**
    - One-time use enforcement (JTI blacklist)
    - Validates user has access to selected tenant
    - Short-lived temp tokens (5 min expiry)
    - Tenant existence and active status verification

    **Rate Limit**: 10 requests per minute per IP

    - **temp_token**: Temporary JWT from /login-and-discover
    - **selected_subdomain**: User-selected tenant subdomain
    """

    try:
        # Step 1: Decode and validate temporary token
        payload = decode_access_token(exchange_request.temp_token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        # Verify this is a temporary token
        if not payload.get("temp"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not a temporary token"
            )

        # Extract JTI for one-time use check
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token missing JTI claim"
            )

        # Step 2: Check if token has already been used (one-time use enforcement)
        token_blacklist = get_token_blacklist()
        if token_blacklist.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has already been used"
            )

        # Step 3: Get user info from token
        user_id = payload.get("sub")
        user_email = payload.get("email")
        user_role = payload.get("role")

        if not all([user_id, user_email, user_role]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token missing required claims"
            )

        # Step 4: Verify tenant exists and is active
        registry_client = create_client(
            settings.tenant_registry_url,
            settings.tenant_registry_anon_key
        )

        tenant_result = registry_client.table('tenants')\
            .select('tenant_id, subdomain, company_name, is_active')\
            .eq('subdomain', exchange_request.selected_subdomain)\
            .execute()

        if not tenant_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant not found: {exchange_request.selected_subdomain}"
            )

        tenant = tenant_result.data[0]

        if not tenant['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant is inactive"
            )

        # Step 5: Verify user has access to selected tenant (by email)
        user_tenant_result = registry_client.table('user_tenants')\
            .select('*')\
            .eq('email', user_email.lower())\
            .eq('tenant_id', tenant['tenant_id'])\
            .execute()

        if not user_tenant_result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this tenant"
            )

        # Step 6: Blacklist the temp token (one-time use)
        token_blacklist.add_to_blacklist(jti, ttl=300)  # 5 min TTL

        # Step 7: Create real JWT token with tenant claims
        access_token = create_access_token(
            data={
                "sub": user_id,
                "email": user_email,
                "role": user_role
            },
            tenant_id=tenant['tenant_id'],
            subdomain=tenant['subdomain']
        )

        # Step 8: Return token + redirect URL
        redirect_url = f"https://{tenant['subdomain']}.taskifai.com/dashboard"

        return ExchangeTokenResponse(
            access_token=access_token,
            redirect_url=redirect_url,
            subdomain=tenant['subdomain'],
            company_name=tenant['company_name']
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token exchange failed: {str(e)}"
        )

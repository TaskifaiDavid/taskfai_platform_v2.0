"""
FastAPI Dependencies for authentication and database access
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.core.config import settings
from app.core.security import decode_access_token
from app.core.tenant import TenantContext, TenantContextManager

# Security scheme for JWT Bearer tokens
security = HTTPBearer()


def get_tenant_context(request: Request) -> TenantContext:
    """
    Get tenant context from request

    For demo mode: Returns demo tenant
    For production: Extracts subdomain and loads tenant config

    Args:
        request: FastAPI request object

    Returns:
        TenantContext
    """
    # Extract subdomain from hostname
    hostname = request.headers.get("host", "localhost")
    subdomain = TenantContextManager.extract_subdomain(hostname)

    # For demo mode, always return demo context
    if subdomain == "demo" or subdomain is None:
        return TenantContextManager.get_demo_context()

    # Future: Load tenant from registry
    # For now, return demo
    return TenantContextManager.get_demo_context()


def get_supabase_client(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)]
) -> Client:
    """
    Create Supabase client instance for tenant

    Args:
        tenant_context: Tenant context from request

    Returns:
        Configured Supabase client for tenant's database
    """
    # For demo mode, use configured database with SERVICE key
    # Service key bypasses RLS, which is needed for auth operations
    if tenant_context.is_demo:
        return create_client(
            settings.supabase_url,
            settings.supabase_service_key  # Changed from anon_key
        )

    # For production tenants, use tenant-specific database
    # (Future implementation - load from tenant registry)
    if tenant_context.database_url and tenant_context.database_key:
        return create_client(
            tenant_context.database_url,
            tenant_context.database_key
        )

    # Fallback to demo database
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key  # Changed from anon_key
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: Annotated[Client, Depends(get_supabase_client)]
) -> dict:
    """
    Validate JWT token and return current user

    Args:
        credentials: HTTP Bearer token from request header
        supabase: Supabase client instance

    Returns:
        User data dict with user_id, email, and role

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # Extract user_id from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()

        if not response.data:
            raise credentials_exception

        user = response.data[0]
        return user

    except Exception:
        raise credentials_exception


# Alias for backwards compatibility
async def get_tenant_db_pool(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)]
) -> Client:
    """Alias for get_supabase_client for backwards compatibility"""
    return get_supabase_client(tenant_context)


async def require_admin(
    user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Require admin role for endpoint"""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Type alias for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
SupabaseClient = Annotated[Client, Depends(get_supabase_client)]
CurrentTenant = Annotated[TenantContext, Depends(get_tenant_context)]

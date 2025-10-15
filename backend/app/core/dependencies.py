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
    Get tenant context from request.state (set by TenantContextMiddleware)

    This dependency retrieves the tenant context that was already resolved
    by TenantContextMiddleware and stored in request.state.tenant.

    Args:
        request: FastAPI request object

    Returns:
        TenantContext from request.state

    Raises:
        HTTPException: If tenant context not found in request state
    """
    # Get tenant context from middleware
    if not hasattr(request.state, "tenant"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant context not found in request state. TenantContextMiddleware may not be registered."
        )

    return request.state.tenant


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
def get_tenant_db_pool(
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


async def require_super_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """
    Require super admin access for endpoint

    Validates JWT token and checks if user email exists in super_admins table.
    This allows separation between regular tenant admins and platform super admins.

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        Token payload with user information

    Raises:
        HTTPException: If token invalid or user is not a super admin
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Super admin access required. Contact platform administrator."
    )

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # Extract email from token
    email = payload.get("email")
    if not email:
        raise credentials_exception

    # Check if email exists in super_admins table (tenant registry database)
    try:
        registry_client = create_client(
            settings.get_tenant_registry_url(),
            settings.get_tenant_registry_service_key()
        )

        response = registry_client.table("super_admins")\
            .select("email")\
            .eq("email", email.lower())\
            .execute()

        if not response.data:
            # User not in super_admins allowlist
            raise forbidden_exception

    except HTTPException:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Database connection or query error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify super admin status: {str(e)}"
        )

    return payload


async def get_user_role_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> Optional[str]:
    """
    Extract user role from JWT token

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        User role (member, admin, super_admin) or None if not present
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        return None

    return payload.get("role")


# Type alias for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
SupabaseClient = Annotated[Client, Depends(get_supabase_client)]
CurrentTenant = Annotated[TenantContext, Depends(get_tenant_context)]
SuperAdmin = Annotated[dict, Depends(require_super_admin)]

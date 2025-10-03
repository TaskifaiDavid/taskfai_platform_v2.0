"""
FastAPI Dependencies for authentication and database access
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.core.config import settings
from app.core.security import decode_access_token

# Security scheme for JWT Bearer tokens
security = HTTPBearer()


def get_supabase_client() -> Client:
    """
    Create Supabase client instance

    Returns:
        Configured Supabase client
    """
    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key
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


# Type alias for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
SupabaseClient = Annotated[Client, Depends(get_supabase_client)]

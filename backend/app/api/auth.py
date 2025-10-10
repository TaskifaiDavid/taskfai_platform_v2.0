"""
Authentication endpoints for user registration and login
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import SupabaseClient
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import AuthResponse, UserCreate, UserLogin, UserResponse

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

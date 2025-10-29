"""
Authentication Middleware

Validates JWT tokens and ensures tenant_id in token matches request tenant.
Injects authenticated user into request.state.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional

from app.core.security import decode_access_token
from app.core.tenant import TenantContext


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT tokens and enforce tenant security

    Flow:
    1. Extract JWT from Authorization header
    2. Decode and validate token
    3. Verify tenant_id in token matches request tenant
    4. Inject user data into request.state
    """

    # Paths that don't require authentication
    # NOTE: Includes both /api/* and /* variants to handle:
    # - Local dev: Direct backend access uses /api/* paths
    # - Production: DigitalOcean App Platform routes may strip /api prefix
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/api/health",  # Support both /health and /api/health for DigitalOcean compatibility
        "/api/docs",
        "/api/redoc",
        "/openapi.json",
        # Diagnostic endpoint
        "/api/debug/tenant",
        # Multi-tenant backend discovery (must be public - called before authentication)
        "/api/discover-backend",
        # Auth endpoints - with /api prefix (local dev)
        "/api/auth/login",
        "/api/auth/register",
        # Auth endpoints - without /api prefix (production route rewriting)
        "/auth/login",
        "/auth/register"
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and validate authentication

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from downstream handler

        Raises:
            HTTPException: If authentication fails
        """
        # Skip auth for OPTIONS preflight requests (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # DEBUG: Log request path to diagnose PUBLIC_PATHS matching
        print(f"[AuthMiddleware] Checking path: '{request.url.path}'")
        print(f"[AuthMiddleware] Is public? {request.url.path in self.PUBLIC_PATHS}")

        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            print(f"[AuthMiddleware] ✓ Skipping auth for public path: {request.url.path}")
            return await call_next(request)

        print(f"[AuthMiddleware] ✗ Requiring auth for path: {request.url.path}")

        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Parse Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )

        token = parts[1]

        # Decode token
        payload = decode_access_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Verify tenant_id claim matches request tenant
        token_tenant_id = payload.get("tenant_id")
        token_subdomain = payload.get("subdomain")

        # Get tenant from request state (set by TenantContextMiddleware)
        if not hasattr(request.state, "tenant"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant context not found in request"
            )

        request_tenant: TenantContext = request.state.tenant

        # Validate tenant claims
        # Special case for BIBBI: Accept both "bibbi" (old tokens) and UUID (new tenant_id)
        is_bibbi_match = (
            request_tenant.subdomain == "bibbi" and
            token_tenant_id in ("bibbi", "5d15bb52-7fef-4b56-842d-e752f3d01292")
        )

        if not is_bibbi_match and token_tenant_id != request_tenant.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token tenant mismatch - possible cross-tenant attack"
            )

        if token_subdomain != request_tenant.subdomain:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token subdomain mismatch - possible subdomain spoofing"
            )

        # Inject user data into request state
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        request.state.user_role = payload.get("role", "analyst")

        # Continue to next handler
        response = await call_next(request)
        return response


def get_current_user_id(request: Request) -> str:
    """
    Helper to get current user ID from request

    Args:
        request: FastAPI request

    Returns:
        User ID from JWT token

    Raises:
        HTTPException: If user not authenticated
    """
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )

    return request.state.user_id


def get_current_user_email(request: Request) -> str:
    """
    Helper to get current user email from request

    Args:
        request: FastAPI request

    Returns:
        User email from JWT token

    Raises:
        HTTPException: If user not authenticated
    """
    if not hasattr(request.state, "user_email"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )

    return request.state.user_email


def require_admin(request: Request) -> bool:
    """
    Check if current user has admin role

    Args:
        request: FastAPI request

    Returns:
        True if user is admin

    Raises:
        HTTPException: If user is not admin
    """
    role = getattr(request.state, "user_role", "analyst")

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return True

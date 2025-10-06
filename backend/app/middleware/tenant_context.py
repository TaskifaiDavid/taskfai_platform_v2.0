"""
Tenant Context Middleware

Extracts subdomain from request hostname and resolves tenant context.
Injects tenant into request.state for use by downstream handlers.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.tenant import TenantContextManager, TenantContext


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant context from subdomain

    Flow:
    1. Extract subdomain from request hostname
    2. Lookup tenant from registry
    3. Validate tenant is active
    4. Inject TenantContext into request.state
    """

    def __init__(self, app):
        super().__init__(app)
        self.tenant_manager = TenantContextManager()

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and inject tenant context

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from downstream handler

        Raises:
            HTTPException: If tenant not found or inactive
        """
        # Extract subdomain from hostname
        hostname = request.headers.get("host", "").split(":")[0]
        subdomain = TenantContextManager.extract_subdomain(hostname)

        try:
            # Resolve tenant context from subdomain
            tenant_context = await self.tenant_manager.from_subdomain(subdomain)

            # Inject into request state
            request.state.tenant = tenant_context

        except ValueError as e:
            # Tenant not found or inactive
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant error: {str(e)}"
            )
        except Exception as e:
            # Other errors (database, etc.)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resolve tenant: {str(e)}"
            )

        # Continue to next handler
        response = await call_next(request)
        return response


def get_tenant_from_request(request: Request) -> TenantContext:
    """
    Helper function to get tenant context from request

    Usage in route handlers:
        tenant = get_tenant_from_request(request)

    Args:
        request: FastAPI request

    Returns:
        TenantContext from request.state

    Raises:
        HTTPException: If tenant not found in request state
    """
    if not hasattr(request.state, "tenant"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant context not found in request"
        )

    return request.state.tenant

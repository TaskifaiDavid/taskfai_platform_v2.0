"""
Tenant Context Middleware

Extracts subdomain from request hostname and resolves tenant context.
Injects tenant into request.state for use by downstream handlers.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
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
        # Skip tenant resolution for OPTIONS preflight requests (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip tenant resolution for health/root/debug endpoints only
        # All auth endpoints now require tenant context (tenant-specific login)
        skip_paths = [
            "/health",  # Health check endpoint (App Platform & Docker)
            "/",  # Root endpoint
            "/api/debug/tenant",  # Debug endpoint for troubleshooting tenant context
        ]
        if request.url.path in skip_paths:
            return await call_next(request)

        # Check for tenant override (production deployments)
        # This allows forcing a specific tenant_id regardless of URL detection
        # Useful for DigitalOcean deployments where URLs don't follow subdomain pattern
        if settings.tenant_id_override:
            print(f"[TenantContextMiddleware] Using TENANT_ID_OVERRIDE: {settings.tenant_id_override}")

            if settings.tenant_id_override == "bibbi":
                request.state.tenant = TenantContextManager.get_bibbi_context()
                print(f"[TenantContextMiddleware] Set BIBBI tenant via override: {request.state.tenant}")
            elif settings.tenant_id_override == "demo":
                request.state.tenant = TenantContextManager.get_demo_context()
                print(f"[TenantContextMiddleware] Set demo tenant via override: {request.state.tenant}")
            else:
                # Custom tenant - lookup from registry
                try:
                    print(f"[TenantContextMiddleware] Looking up custom tenant: {settings.tenant_id_override}")
                    tenant_context = await self.tenant_manager.from_subdomain(settings.tenant_id_override)
                    request.state.tenant = tenant_context
                    print(f"[TenantContextMiddleware] Set custom tenant via override: {tenant_context}")
                except ValueError as e:
                    print(f"[TenantContextMiddleware] Override tenant not found: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Tenant override error: {str(e)}"
                    )

            # Continue to next handler with overridden tenant
            response = await call_next(request)
            return response

        # Extract subdomain from hostname (default behavior when no override)
        hostname = request.headers.get("host", "").split(":")[0]
        subdomain = TenantContextManager.extract_subdomain(hostname)

        print(f"[TenantContextMiddleware] hostname={hostname}, subdomain={subdomain}")

        # For demo/localhost/app, always use demo context without database lookup
        # This ensures local development works even if tenant registry is not set up
        # "app" subdomain is the central login portal at app.taskifai.com
        # "bibbi" subdomain is for local testing of BIBBI tenant features
        if subdomain in ("demo", "localhost", "app", None):
            print(f"[TenantContextMiddleware] Using demo context for subdomain: {subdomain}")
            request.state.tenant = TenantContextManager.get_demo_context()
            print(f"[TenantContextMiddleware] Set demo tenant: {request.state.tenant}")
        elif subdomain == "bibbi":
            print(f"[TenantContextMiddleware] Using BIBBI context for local testing")
            request.state.tenant = TenantContextManager.get_bibbi_context()
            print(f"[TenantContextMiddleware] Set BIBBI tenant: {request.state.tenant}")
        else:
            # Production tenant - lookup from registry
            try:
                print(f"[TenantContextMiddleware] Looking up tenant for subdomain: {subdomain}")
                tenant_context = await self.tenant_manager.from_subdomain(subdomain)
                request.state.tenant = tenant_context
                print(f"[TenantContextMiddleware] Set tenant: {tenant_context}")

            except ValueError as e:
                # Tenant not found or inactive
                print(f"[TenantContextMiddleware] ValueError: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant error: {str(e)}"
                )
            except Exception as e:
                # Other errors (database, etc.)
                print(f"[TenantContextMiddleware] Exception: {e}")
                import traceback
                traceback.print_exc()

                # SECURITY: Only fallback to demo in development mode
                # In production, reject requests to prevent tenant bypass attacks
                if settings.debug:
                    # Development mode - fallback to demo for convenience
                    print(f"[TenantContextMiddleware] DEBUG mode: Falling back to demo context")
                    request.state.tenant = TenantContextManager.get_demo_context()
                else:
                    # Production mode - reject request to prevent bypass
                    print(f"[TenantContextMiddleware] PRODUCTION mode: Rejecting request due to tenant resolution error")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Tenant service temporarily unavailable. Please try again later."
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

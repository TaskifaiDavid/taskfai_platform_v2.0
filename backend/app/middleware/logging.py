"""
Logging Middleware

Logs request/response information for auditing and debugging.
Includes tenant_id, user_id, path, status, and duration.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configure logger
logger = logging.getLogger("taskifai.requests")
logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request/response details

    Logs:
    - Tenant ID and subdomain
    - User ID (if authenticated)
    - Request method and path
    - Response status code
    - Request duration
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and log details

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from downstream handler
        """
        # Start timer
        start_time = time.time()

        # Extract tenant info (if available)
        tenant_id = "unknown"
        subdomain = "unknown"
        if hasattr(request.state, "tenant"):
            tenant_id = request.state.tenant.tenant_id
            subdomain = request.state.tenant.subdomain

        # Extract user info (if authenticated)
        user_id = "anonymous"
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        # Log request
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"tenant={subdomain}({tenant_id}) user={user_id}"
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"tenant={subdomain}({tenant_id}) user={user_id} "
                f"error={str(e)} duration={duration:.3f}s"
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"← {request.method} {request.url.path} "
            f"tenant={subdomain}({tenant_id}) user={user_id} "
            f"status={response.status_code} duration={duration:.3f}s"
        )

        # Add custom headers for debugging
        response.headers["X-Request-Duration"] = f"{duration:.3f}"
        response.headers["X-Tenant-ID"] = tenant_id

        return response

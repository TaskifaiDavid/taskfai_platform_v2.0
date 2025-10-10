"""
FastAPI Dependencies for Rate Limiting

Provides reusable rate limiting dependencies to eliminate code duplication
across API endpoints. Uses the in-memory RateLimiter for single-instance deployments.

For production with multiple instances, replace with Redis-based rate limiting.
"""

from typing import Callable
from fastapi import HTTPException, Request, status
from app.core.rate_limiter import get_rate_limiter


def rate_limit(
    endpoint_name: str,
    max_requests: int = 10,
    window_seconds: int = 60
) -> Callable:
    """
    Create a rate limiting dependency for FastAPI endpoints

    Usage:
        @router.post("/login")
        async def login(
            credentials: UserLogin,
            _: Annotated[None, Depends(rate_limit("login", max_requests=10, window_seconds=60))]
        ):
            # Endpoint logic here

    Args:
        endpoint_name: Descriptive name for the endpoint (used in rate limit key)
        max_requests: Maximum requests allowed in window (default: 10)
        window_seconds: Time window in seconds (default: 60)

    Returns:
        FastAPI dependency function

    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
    """
    async def rate_limit_dependency(request: Request) -> None:
        """Check rate limit for incoming request"""
        # Extract client IP
        client_ip = request.client.host if request.client else "unknown"

        # Get rate limiter instance
        rate_limiter = get_rate_limiter()

        # Check if rate limited
        is_limited, retry_after = rate_limiter.is_rate_limited(
            key=f"{endpoint_name}:{client_ip}",
            max_requests=max_requests,
            window_seconds=window_seconds
        )

        # Raise exception if limited
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

    return rate_limit_dependency


# Pre-configured rate limiters for common endpoints
def auth_rate_limit(request: Request) -> None:
    """
    Rate limiter for authentication endpoints (login, register)

    Limit: 10 requests per minute per IP
    """
    return rate_limit("auth", max_requests=10, window_seconds=60)(request)


def discovery_rate_limit(request: Request) -> None:
    """
    Rate limiter for tenant discovery endpoint

    Limit: 10 requests per minute per IP
    Prevents email enumeration attacks
    """
    return rate_limit("discover", max_requests=10, window_seconds=60)(request)


def token_exchange_rate_limit(request: Request) -> None:
    """
    Rate limiter for token exchange endpoint

    Limit: 10 requests per minute per IP
    """
    return rate_limit("exchange", max_requests=10, window_seconds=60)(request)

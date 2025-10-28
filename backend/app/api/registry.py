# ABOUTME: Backend discovery service for multi-tenant routing
# ABOUTME: Returns correct backend URL based on tenant subdomain

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/discover-backend")
async def discover_backend(subdomain: str):
    """
    Discover which backend URL to use for a given tenant subdomain.

    This enables one frontend to dynamically route to different tenant-specific backends.

    Args:
        subdomain: Tenant subdomain (e.g., "demo", "bibbi")

    Returns:
        {
            "backend_url": "https://tenant-backend.ondigitalocean.app",
            "subdomain": "demo"
        }

    Raises:
        HTTPException: 404 if subdomain not recognized

    Example:
        GET /api/discover-backend?subdomain=bibbi
        -> {"backend_url": "https://taskifai-bibbi-3lmi3.ondigitalocean.app", "subdomain": "bibbi"}
    """
    # Subdomain to backend URL mapping
    # TODO: Move to database (tenants.backend_url column) for true scalability
    backend_map = {
        "demo": "https://taskifai-demo-ak4kq.ondigitalocean.app",
        "bibbi": "https://taskifai-bibbi-3lmi3.ondigitalocean.app"
    }

    backend_url = backend_map.get(subdomain)

    if not backend_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown tenant subdomain: {subdomain}"
        )

    return {
        "backend_url": backend_url,
        "subdomain": subdomain
    }

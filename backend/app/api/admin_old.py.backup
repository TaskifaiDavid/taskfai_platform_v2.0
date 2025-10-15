"""
Admin endpoints for platform administration and tenant management
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, require_admin
from app.models.user import UserResponse
from app.models.tenant import TenantCreate, TenantUpdate, Tenant
from app.services.tenant.provisioner import TenantProvisioner
from app.services.tenant.manager import TenantManager


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.post("/tenants", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Provision new tenant (Admin only)

    Steps:
    1. Create Supabase project
    2. Apply schema migrations
    3. Seed vendor configurations
    4. Register in master registry

    - **subdomain**: Unique subdomain for tenant
    - **organization_name**: Organization display name
    - **admin_email**: Admin user email
    - **database_url**: Database connection URL (optional, auto-provisioned if not provided)
    - **database_key**: Database password (optional, auto-provisioned if not provided)

    If database credentials not provided, will automatically provision via Supabase Management API.
    """
    try:
        provisioner = TenantProvisioner()

        # Check if auto-provisioning (no DB credentials provided)
        if not tenant_data.database_url or not tenant_data.database_key:
            # Auto-provision via Supabase Management API
            tenant = await provisioner.provision_tenant(
                subdomain=tenant_data.subdomain,
                organization_name=tenant_data.organization_name,
                admin_email=tenant_data.admin_email,
                region="us-east-1"
            )
        else:
            # Manual registration with provided credentials
            from app.services.tenant.registry import TenantRegistry
            registry = TenantRegistry()
            tenant = await registry.create_tenant(tenant_data)

        return tenant

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tenant creation failed: {str(e)}"
        )


@router.get("/tenants", response_model=list[dict], status_code=status.HTTP_200_OK)
async def list_tenants(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100
):
    """
    List all tenants with stats (Admin only)

    - **active_only**: Return only active tenants (default: False)
    - **skip**: Pagination offset
    - **limit**: Results per page (max 100)

    Returns list of tenants with:
    - Basic info (subdomain, organization name, status)
    - Connection status
    - Creation date
    """
    try:
        manager = TenantManager()

        tenants = await manager.list_all_tenants(
            active_only=active_only,
            skip=skip,
            limit=min(limit, 100)
        )

        return tenants

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )


@router.get("/tenants/{tenant_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_tenant_details(
    tenant_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Get detailed tenant information (Admin only)

    Returns:
    - Tenant configuration
    - Usage statistics (users, uploads, sales records)
    - Last activity timestamp
    - Connection health
    """
    try:
        manager = TenantManager()

        # Get tenant stats
        stats = await manager.get_tenant_stats(tenant_id)

        # Get health check
        health = await manager.health_check_tenant(tenant_id)

        return {
            **stats,
            'health': health
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant details: {str(e)}"
        )


@router.patch("/tenants/{tenant_id}/suspend", response_model=Tenant, status_code=status.HTTP_200_OK)
async def suspend_tenant(
    tenant_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    reason: Optional[str] = None
):
    """
    Suspend a tenant (Admin only)

    - **tenant_id**: Tenant to suspend
    - **reason**: Suspension reason (optional)

    This will:
    1. Mark tenant as inactive
    2. Invalidate all active connections
    3. Clear credential cache
    4. Block all API access for tenant users

    Suspended tenants can be reactivated later.
    """
    try:
        manager = TenantManager()

        suspended_tenant = await manager.suspend_tenant(
            tenant_id=tenant_id,
            reason=reason
        )

        return suspended_tenant

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suspend tenant: {str(e)}"
        )


@router.patch("/tenants/{tenant_id}/reactivate", response_model=Tenant, status_code=status.HTTP_200_OK)
async def reactivate_tenant(
    tenant_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Reactivate a suspended tenant (Admin only)

    - **tenant_id**: Tenant to reactivate

    This will:
    1. Mark tenant as active
    2. Clear suspension metadata
    3. Allow API access for tenant users

    Database connections will be recreated on next request.
    """
    try:
        manager = TenantManager()

        reactivated_tenant = await manager.reactivate_tenant(tenant_id)

        return reactivated_tenant

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reactivate tenant: {str(e)}"
        )


@router.put("/tenants/{tenant_id}", response_model=Tenant, status_code=status.HTTP_200_OK)
async def update_tenant(
    tenant_id: UUID,
    update_data: TenantUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Update tenant configuration (Admin only)

    - **organization_name**: Update organization name
    - **admin_email**: Update admin email
    - **database_url**: Update database URL (will invalidate connections)
    - **database_key**: Update database password (will invalidate connections)

    Only provided fields will be updated.
    Changing database credentials will invalidate active connections.
    """
    try:
        manager = TenantManager()

        updated_tenant = await manager.update_tenant_details(
            tenant_id=tenant_id,
            update_data=update_data
        )

        return updated_tenant

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )


@router.get("/tenants/{tenant_id}/health", response_model=dict, status_code=status.HTTP_200_OK)
async def check_tenant_health(
    tenant_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Check tenant infrastructure health (Admin only)

    Performs health checks on:
    - Database connectivity
    - RLS policy status
    - Connection pool status

    Returns detailed health status for debugging.
    """
    try:
        manager = TenantManager()

        health = await manager.health_check_tenant(tenant_id)

        return health

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

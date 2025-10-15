"""
Tenant Administration API Endpoints

Super admin endpoints for managing tenants in the multi-tenant registry.

All endpoints require super_admin role in JWT token.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client, create_client

from app.core.config import settings
from app.core.dependencies import SuperAdmin
from app.models.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.models.user_tenant import UserTenantCreate, UserTenantResponse
from app.services.tenant_registry import TenantRegistryService

router = APIRouter(prefix="/admin/tenants", tags=["admin", "tenants"])


def get_tenant_registry_client() -> Client:
    """
    Get Supabase client for tenant registry database

    Returns:
        Configured Supabase client for registry
    """
    return create_client(
        settings.get_tenant_registry_url(),
        settings.get_tenant_registry_service_key()
    )


def get_tenant_registry_service(
    registry_client: Annotated[Client, Depends(get_tenant_registry_client)]
) -> TenantRegistryService:
    """
    Get tenant registry service instance

    Args:
        registry_client: Supabase client for registry

    Returns:
        TenantRegistryService instance
    """
    return TenantRegistryService(registry_client)


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new tenant",
    description="Create a new tenant with encrypted credentials. Requires super_admin role."
)
async def create_tenant(
    tenant_data: TenantCreate,
    admin_user: SuperAdmin,
    registry_service: Annotated[TenantRegistryService, Depends(get_tenant_registry_service)]
) -> TenantResponse:
    """
    Create new tenant in registry

    - Validates subdomain availability
    - Encrypts database credentials using pgcrypto
    - Creates admin user mapping
    - Returns tenant information (without credentials)

    **Required JWT role:** super_admin
    """
    try:
        tenant = registry_service.create_tenant(tenant_data)
        return tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.get(
    "/",
    response_model=dict,
    summary="List all tenants",
    description="List all tenants with pagination. Requires super_admin role."
)
async def list_tenants(
    admin_user: SuperAdmin,
    registry_service: Annotated[TenantRegistryService, Depends(get_tenant_registry_service)],
    limit: int = Query(default=10, ge=1, le=100, description="Number of tenants per page"),
    offset: int = Query(default=0, ge=0, description="Offset from start"),
    active_only: bool = Query(default=False, description="Only return active tenants")
) -> dict:
    """
    List all tenants with pagination

    **Required JWT role:** super_admin

    **Query Parameters:**
    - limit: Number of tenants per page (1-100, default: 10)
    - offset: Offset from start (default: 0)
    - active_only: Only return active tenants (default: false)

    **Returns:**
    - tenants: List of tenant objects
    - total: Total number of tenants
    - limit: Requested limit
    - offset: Requested offset
    """
    try:
        tenants, total = registry_service.list_tenants(
            limit=limit,
            offset=offset,
            active_only=active_only
        )

        return {
            "tenants": tenants,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant details",
    description="Get detailed information for specific tenant. Requires super_admin role."
)
async def get_tenant(
    tenant_id: UUID,
    admin_user: SuperAdmin,
    registry_service: Annotated[TenantRegistryService, Depends(get_tenant_registry_service)]
) -> TenantResponse:
    """
    Get tenant details by ID

    **Required JWT role:** super_admin

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Returns:**
    Tenant information (without credentials)
    """
    try:
        tenant = registry_service.get_tenant_by_id(tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

        return tenant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant: {str(e)}"
        )


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant",
    description="Update tenant information (activate/suspend, update details). Requires super_admin role."
)
async def update_tenant(
    tenant_id: UUID,
    tenant_update: TenantUpdate,
    admin_user: SuperAdmin,
    registry_service: Annotated[TenantRegistryService, Depends(get_tenant_registry_service)]
) -> TenantResponse:
    """
    Update tenant information

    **Required JWT role:** super_admin

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Request Body:**
    - company_name: Updated company name (optional)
    - database_url: Updated database URL (optional)
    - database_credentials: Updated credentials (optional, will be encrypted)
    - is_active: Activate (true) or suspend (false) tenant (optional)
    - metadata: Custom metadata (optional)

    **Use Cases:**
    - Suspend tenant: `{"is_active": false}`
    - Reactivate tenant: `{"is_active": true}`
    - Update company name: `{"company_name": "New Name"}`
    - Update credentials: `{"database_credentials": {"anon_key": "...", "service_key": "..."}}`
    """
    try:
        tenant = registry_service.update_tenant(tenant_id, tenant_update)
        return tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )


@router.post(
    "/{tenant_id}/users",
    status_code=status.HTTP_201_CREATED,
    summary="Add user to tenant",
    description="Add user to tenant with specified role. Requires super_admin role."
)
async def add_user_to_tenant(
    tenant_id: UUID,
    user_tenant: UserTenantCreate,
    admin_user: SuperAdmin,
    registry_service: Annotated[TenantRegistryService, Depends(get_tenant_registry_service)]
) -> dict:
    """
    Add user to tenant

    **Required JWT role:** super_admin

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Request Body:**
    - email: User email address
    - role: User role (member, admin, super_admin)

    **Returns:**
    Success message
    """
    try:
        # Verify tenant exists
        tenant = registry_service.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

        # Add user to tenant
        registry_service.add_user_to_tenant(tenant_id, user_tenant)

        return {
            "message": f"User {user_tenant.email} added to tenant {tenant_id}",
            "email": user_tenant.email,
            "role": user_tenant.role,
            "tenant_id": str(tenant_id)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add user to tenant: {str(e)}"
        )

"""
Dashboard configuration endpoints for BI tool embedding
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, get_tenant_db_pool
from app.models.user import UserResponse
from app.models.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardList,
    DashboardEmbedRequest,
    DashboardEmbedResponse
)
from app.services.dashboard.manager import DashboardManager
from app.services.dashboard.validator import DashboardURLValidator
from supabase import Client


router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard: DashboardCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)]
):
    """
    Create new dashboard configuration

    - **dashboard_name**: Display name for dashboard
    - **dashboard_type**: Type of BI tool (looker, metabase, powerbi, etc.)
    - **dashboard_url**: URL to embed
    - **auth_config**: Optional authentication configuration (will be encrypted)
    - **is_primary**: Set as primary dashboard (only one can be primary)

    Dashboard URLs are validated for security (HTTPS required, localhost blocked in production)
    """
    try:
        manager = DashboardManager(supabase)
        validator = DashboardURLValidator()

        # Validate URL
        validation = await validator.validate_url(dashboard.dashboard_url)
        if not validation['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dashboard URL: {validation['reason']}"
            )

        # Create dashboard
        created = await manager.create_dashboard(
            user_id=UUID(current_user.user_id),
            dashboard_data=dashboard
        )

        return created

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard: {str(e)}"
        )


@router.get("", response_model=DashboardList, status_code=status.HTTP_200_OK)
async def list_dashboards(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)],
    skip: int = 0,
    limit: int = 50
):
    """
    List all dashboards for current user

    - **skip**: Pagination offset
    - **limit**: Number of dashboards to return (max 100)

    Returns dashboards sorted with primary dashboard first
    """
    try:
        manager = DashboardManager(supabase)

        dashboards = await manager.list_dashboards(
            user_id=UUID(current_user.user_id),
            skip=skip,
            limit=min(limit, 100)
        )

        return DashboardList(
            dashboards=dashboards,
            total=len(dashboards),
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list dashboards: {str(e)}"
        )


@router.get("/{dashboard_id}", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
async def get_dashboard(
    dashboard_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)]
):
    """
    Get dashboard details by ID

    Returns dashboard configuration with decrypted auth (if user has permission)
    """
    try:
        manager = DashboardManager(supabase)

        dashboard = await manager.get_dashboard(
            dashboard_id=dashboard_id,
            user_id=UUID(current_user.user_id)
        )

        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )

        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


@router.put("/{dashboard_id}", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
async def update_dashboard(
    dashboard_id: UUID,
    update: DashboardUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)]
):
    """
    Update dashboard configuration

    - **dashboard_name**: Update display name
    - **dashboard_url**: Update embed URL (will be validated)
    - **auth_config**: Update auth configuration
    - **is_active**: Enable/disable dashboard

    Only fields provided in request will be updated
    """
    try:
        manager = DashboardManager(supabase)
        validator = DashboardURLValidator()

        # Validate new URL if provided
        if update.dashboard_url:
            validation = await validator.validate_url(update.dashboard_url)
            if not validation['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid dashboard URL: {validation['reason']}"
                )

        # Update dashboard
        updated = await manager.update_dashboard(
            dashboard_id=dashboard_id,
            user_id=UUID(current_user.user_id),
            update_data=update
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )

        return updated

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dashboard: {str(e)}"
        )


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)]
):
    """
    Delete dashboard configuration

    This will permanently delete the dashboard configuration.
    """
    try:
        manager = DashboardManager(supabase)

        deleted = await manager.delete_dashboard(
            dashboard_id=dashboard_id,
            user_id=UUID(current_user.user_id)
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dashboard: {str(e)}"
        )


@router.patch("/{dashboard_id}/primary", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
async def set_primary_dashboard(
    dashboard_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)]
):
    """
    Set dashboard as primary

    Only one dashboard can be primary at a time.
    Setting a new primary will unset the previous primary.
    """
    try:
        manager = DashboardManager(supabase)

        updated = await manager.set_primary_dashboard(
            dashboard_id=dashboard_id,
            user_id=UUID(current_user.user_id)
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )

        return updated

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set primary dashboard: {str(e)}"
        )


@router.post("/embed", response_model=DashboardEmbedResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_embed_url(
    request: DashboardEmbedRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)]
):
    """
    Get secure embed URL with authentication for iframe display

    - **dashboard_id**: Dashboard to embed

    Returns URL with embedded authentication for secure iframe display
    """
    try:
        manager = DashboardManager(supabase)

        embed_response = await manager.get_embed_url(
            dashboard_id=request.dashboard_id,
            user_id=UUID(current_user.user_id)
        )

        if not embed_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )

        return embed_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embed URL: {str(e)}"
        )

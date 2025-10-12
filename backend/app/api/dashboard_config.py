"""
Dashboard Configuration API Endpoints

Implements Option 1: Database-Driven Dashboards
Provides dynamic dashboard configuration per user/tenant.
"""

from typing import Annotated, Optional
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.dependencies import get_current_user, get_supabase_client
from app.models.user import UserResponse
from app.models.dashboard_config import (
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigResponse,
    DashboardConfigListResponse,
    DashboardConfigSummary
)


router = APIRouter(prefix="/dashboard-configs", tags=["Dashboard Configuration"])


@router.get("/default", response_model=DashboardConfigResponse, status_code=status.HTTP_200_OK)
async def get_default_dashboard_config(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase_client)]
):
    """
    Get default dashboard configuration for current user.
    
    Priority order:
    1. User's personal default (is_default=true, user_id=current_user)
    2. Tenant-wide default (is_default=true, user_id=NULL)
    
    Returns 404 if no default configuration exists.
    """
    try:
        # First, try to get user-specific default
        response = supabase.table("dynamic_dashboard_configs") \
            .select("*") \
            .eq("user_id", current_user["user_id"]) \
            .eq("is_default", True) \
            .eq("is_active", True) \
            .maybe_single() \
            .execute()

        # If no user-specific default, get tenant-wide default
        if not response.data:
            response = supabase.table("dynamic_dashboard_configs") \
                .select("*") \
                .is_("user_id", None) \
                .eq("is_default", True) \
                .eq("is_active", True) \
                .maybe_single() \
                .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No default dashboard configuration found"
            )
        
        # Parse JSON fields and convert to proper types
        config = response.data

        # Parse JSON if stored as string, Supabase JSONB usually returns as dict/list already
        layout_data = json.loads(config['layout']) if isinstance(config['layout'], str) else config['layout']
        kpis_data = json.loads(config['kpis']) if isinstance(config['kpis'], str) else config['kpis']
        filters_data = json.loads(config['filters']) if isinstance(config['filters'], str) else config['filters']

        # Build response with Pydantic parsing (let Pydantic handle type conversion)
        return DashboardConfigResponse(
            dashboard_id=config['dashboard_id'],
            user_id=config['user_id'],
            dashboard_name=config['dashboard_name'],
            description=config.get('description'),
            layout=layout_data,  # Pydantic will convert list of dicts to List[WidgetConfig]
            kpis=kpis_data,  # Pydantic will convert list of strings to List[KPIType]
            filters=filters_data,  # Pydantic will convert dict to DashboardFilters
            is_default=config['is_default'],
            is_active=config['is_active'],
            display_order=config['display_order'],
            created_at=config['created_at'],
            updated_at=config['updated_at']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = f"Failed to fetch default dashboard config: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_details}")  # Log to console for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch default dashboard config: {str(e)}"
        )


@router.get("", response_model=DashboardConfigListResponse, status_code=status.HTTP_200_OK)
async def list_dynamic_dashboard_configs(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase_client)],
    include_tenant_defaults: bool = True
):
    """
    List all dashboard configurations for current user.
    
    - **include_tenant_defaults**: Include tenant-wide defaults in results
    
    Returns user's personal configs and optionally tenant-wide defaults.
    """
    try:
        # Build query
        query = supabase.table("dynamic_dashboard_configs").select(
            "dashboard_id, dashboard_name, description, is_default, is_active, "
            "display_order, updated_at, "
            "layout, kpis"
        ).eq("is_active", True)
        
        # Filter by user_id OR tenant defaults
        if include_tenant_defaults:
            # Get both user configs and tenant defaults
            user_configs = supabase.table("dynamic_dashboard_configs") \
                .select("*") \
                .eq("user_id", current_user["user_id"]) \
                .eq("is_active", True) \
                .order("display_order") \
                .execute()
            
            tenant_defaults = supabase.table("dynamic_dashboard_configs") \
                .select("*") \
                .is_("user_id", None) \
                .eq("is_active", True) \
                .order("display_order") \
                .execute()
            
            configs = user_configs.data + tenant_defaults.data
        else:
            # Get only user configs
            response = supabase.table("dynamic_dashboard_configs") \
                .select("*") \
                .eq("user_id", current_user["user_id"]) \
                .eq("is_active", True) \
                .order("display_order") \
                .execute()
            configs = response.data
        
        # Convert to summary models
        summaries = []
        has_default = False
        for config in configs:
            layout = json.loads(config['layout']) if isinstance(config['layout'], str) else config['layout']
            kpis = json.loads(config['kpis']) if isinstance(config['kpis'], str) else config['kpis']
            
            summaries.append(DashboardConfigSummary(
                dashboard_id=config['dashboard_id'],
                dashboard_name=config['dashboard_name'],
                description=config.get('description'),
                is_default=config['is_default'],
                is_active=config['is_active'],
                display_order=config['display_order'],
                widget_count=len(layout) if isinstance(layout, list) else 0,
                kpi_count=len(kpis) if isinstance(kpis, list) else 0,
                updated_at=config['updated_at']
            ))
            
            if config['is_default']:
                has_default = True
        
        return DashboardConfigListResponse(
            dashboards=summaries,
            total=len(summaries),
            has_default=has_default
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list dashboard configs: {str(e)}"
        )


@router.get("/{dashboard_id}", response_model=DashboardConfigResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_config(
    dashboard_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase_client)]
):
    """
    Get specific dashboard configuration by ID.
    
    User can only access their own configs or tenant-wide defaults.
    """
    try:
        # Query with user_id filter OR tenant default
        response = supabase.table("dynamic_dashboard_configs") \
            .select("*") \
            .eq("dashboard_id", str(dashboard_id)) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard configuration not found"
            )
        
        config = response.data[0]
        
        # Security check: user can only access their own configs or tenant defaults
        if config['user_id'] and config['user_id'] != str(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this dashboard configuration"
            )
        
        # Parse JSON fields and convert to proper types
        layout_data = json.loads(config['layout']) if isinstance(config['layout'], str) else config['layout']
        kpis_data = json.loads(config['kpis']) if isinstance(config['kpis'], str) else config['kpis']
        filters_data = json.loads(config['filters']) if isinstance(config['filters'], str) else config['filters']

        # Build response with explicit field mapping
        return DashboardConfigResponse(
            dashboard_id=config['dashboard_id'],
            user_id=config['user_id'],
            dashboard_name=config['dashboard_name'],
            description=config.get('description'),
            layout=layout_data,
            kpis=kpis_data,
            filters=filters_data,
            is_default=config['is_default'],
            is_active=config['is_active'],
            display_order=config['display_order'],
            created_at=config['created_at'],
            updated_at=config['updated_at']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard config: {str(e)}"
        )


@router.post("", response_model=DashboardConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard_config(
    config: DashboardConfigCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase_client)]
):
    """
    Create new dashboard configuration for current user.
    
    - **dashboard_name**: Display name for dashboard
    - **layout**: Array of widget configurations with positions
    - **kpis**: Array of KPI types to display
    - **filters**: Default filter settings
    - **is_default**: Whether this should be the default dashboard
    
    If is_default=true, any existing default will be unset.
    """
    try:
        # If setting as default, unset existing default first
        if config.is_default:
            supabase.table("dynamic_dashboard_configs") \
                .update({"is_default": False}) \
                .eq("user_id", current_user["user_id"]) \
                .eq("is_default", True) \
                .execute()

        # Prepare data for insertion
        insert_data = {
            "user_id": str(current_user["user_id"]),
            "dashboard_name": config.dashboard_name,
            "description": config.description,
            "layout": [widget.model_dump() for widget in config.layout],
            "kpis": [kpi.value for kpi in config.kpis],
            "filters": config.filters.model_dump(),
            "is_default": config.is_default,
            "is_active": config.is_active,
            "display_order": config.display_order
        }
        
        # Insert new config
        response = supabase.table("dynamic_dashboard_configs") \
            .insert(insert_data) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create dashboard configuration"
            )
        
        created = response.data[0]
        return DashboardConfigResponse(**created)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard config: {str(e)}"
        )


@router.put("/{dashboard_id}", response_model=DashboardConfigResponse, status_code=status.HTTP_200_OK)
async def update_dashboard_config(
    dashboard_id: UUID,
    update: DashboardConfigUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase_client)]
):
    """
    Update existing dashboard configuration.
    
    Only the fields provided will be updated.
    User can only update their own configurations.
    """
    try:
        # Check ownership
        check = supabase.table("dynamic_dashboard_configs") \
            .select("user_id") \
            .eq("dashboard_id", str(dashboard_id)) \
            .maybe_single() \
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard configuration not found"
            )

        if check.data['user_id'] != str(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this dashboard configuration"
            )

        # If setting as default, unset existing default
        if update.is_default:
            supabase.table("dynamic_dashboard_configs") \
                .update({"is_default": False}) \
                .eq("user_id", current_user["user_id"]) \
                .eq("is_default", True) \
                .neq("dashboard_id", str(dashboard_id)) \
                .execute()
        
        # Prepare update data (only include non-None fields)
        update_data = {}
        if update.dashboard_name is not None:
            update_data['dashboard_name'] = update.dashboard_name
        if update.description is not None:
            update_data['description'] = update.description
        if update.layout is not None:
            update_data['layout'] = [widget.model_dump() for widget in update.layout]
        if update.kpis is not None:
            update_data['kpis'] = [kpi.value for kpi in update.kpis]
        if update.filters is not None:
            update_data['filters'] = update.filters.model_dump()
        if update.is_default is not None:
            update_data['is_default'] = update.is_default
        if update.is_active is not None:
            update_data['is_active'] = update.is_active
        if update.display_order is not None:
            update_data['display_order'] = update.display_order
        
        # Update config
        response = supabase.table("dynamic_dashboard_configs") \
            .update(update_data) \
            .eq("dashboard_id", str(dashboard_id)) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update dashboard configuration"
            )
        
        updated = response.data[0]
        return DashboardConfigResponse(**updated)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dashboard config: {str(e)}"
        )


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard_config(
    dashboard_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase_client)]
):
    """
    Delete dashboard configuration.
    
    User can only delete their own configurations.
    Cannot delete tenant-wide defaults.
    """
    try:
        # Check ownership
        check = supabase.table("dynamic_dashboard_configs") \
            .select("user_id") \
            .eq("dashboard_id", str(dashboard_id)) \
            .maybe_single() \
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard configuration not found"
            )
        
        # Can't delete tenant defaults
        if not check.data['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete tenant-wide default dashboard"
            )

        if check.data['user_id'] != str(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this dashboard configuration"
            )
        
        # Delete config
        supabase.table("dynamic_dashboard_configs") \
            .delete() \
            .eq("dashboard_id", str(dashboard_id)) \
            .execute()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dashboard config: {str(e)}"
        )

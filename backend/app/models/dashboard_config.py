"""
Dashboard Configuration Models

Pydantic models for dashboard configuration API.
Implements Option 1: Database-Driven Dashboards with strict validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class KPIType(str, Enum):
    """Valid KPI types that can be displayed on dashboards."""
    TOTAL_REVENUE = "total_revenue"
    TOTAL_UNITS = "total_units"
    AVG_PRICE = "avg_price"
    AVERAGE_ORDER_VALUE = "average_order_value"
    UNITS_PER_TRANSACTION = "units_per_transaction"
    FAST_MOVING_PRODUCTS = "fast_moving_products"
    SLOW_MOVING_PRODUCTS = "slow_moving_products"
    TOTAL_UPLOADS = "total_uploads"
    GROSS_PROFIT = "gross_profit"
    PROFIT_MARGIN = "profit_margin"
    UNIQUE_COUNTRIES = "unique_countries"
    ORDER_COUNT = "order_count"
    RESELLER_COUNT = "reseller_count"
    CATEGORY_MIX = "category_mix"
    YOY_GROWTH = "yoy_growth"
    TOP_PRODUCTS = "top_products"


class WidgetType(str, Enum):
    """Valid widget types that can be rendered on dashboards."""
    KPI_GRID = "kpi_grid"
    RECENT_UPLOADS = "recent_uploads"
    TOP_PRODUCTS = "top_products"
    TOP_PRODUCTS_CHART = "top_products_chart"
    RESELLER_PERFORMANCE = "reseller_performance"
    TOP_RESELLERS_CHART = "top_resellers_chart"
    CATEGORY_REVENUE = "category_revenue"
    CHANNEL_MIX = "channel_mix"
    TOP_MARKETS = "top_markets"
    TOP_STORES = "top_stores"
    REVENUE_CHART = "revenue_chart"
    SALES_TREND = "sales_trend"


class WidgetPosition(BaseModel):
    """Widget position and size in grid layout.

    Supports both naming conventions:
    - Frontend: {x, y, w, h} (gridPosition)
    - Backend: {row, col, width, height} (position)
    """
    # Frontend convention (gridPosition)
    x: Optional[int] = Field(None, ge=0, description="Grid X position (column, 0-indexed)")
    y: Optional[int] = Field(None, ge=0, description="Grid Y position (row, 0-indexed)")
    w: Optional[int] = Field(None, ge=1, le=12, description="Widget width in grid columns")
    h: Optional[int] = Field(None, ge=1, le=12, description="Widget height in grid rows")

    # Backend convention (position)
    row: Optional[int] = Field(None, ge=0, description="Grid row position (0-indexed)")
    col: Optional[int] = Field(None, ge=0, le=11, description="Grid column position (0-11)")
    width: Optional[int] = Field(None, ge=1, le=12, description="Widget width in grid columns")
    height: Optional[int] = Field(None, ge=1, le=12, description="Widget height in grid rows")

    @field_validator('w', 'width')
    @classmethod
    def validate_grid_bounds(cls, v: Optional[int], info) -> Optional[int]:
        """Validate that widget fits within 12-column grid."""
        if v is not None and v > 12:
            raise ValueError("Widget width cannot exceed 12 columns")
        return v


class WidgetConfig(BaseModel):
    """Configuration for a single dashboard widget."""
    id: str = Field(..., min_length=1, max_length=100, description="Unique widget identifier")
    type: WidgetType = Field(..., description="Widget type/component to render")
    position: WidgetPosition = Field(..., description="Widget position and size in grid")
    props: Dict[str, Any] = Field(
        default_factory=dict,
        description="Widget-specific properties (title, limit, filters, etc.)"
    )

    @field_validator('props')
    @classmethod
    def validate_props(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate widget props structure."""
        # Ensure common props are valid
        if 'limit' in v and not isinstance(v['limit'], int):
            raise ValueError("Widget 'limit' prop must be an integer")
        if 'title' in v and not isinstance(v['title'], str):
            raise ValueError("Widget 'title' prop must be a string")
        return v


class DashboardFilters(BaseModel):
    """Default filters for dashboard data."""
    date_range: str = Field(
        default="last_30_days",
        description="Default date range filter"
    )
    vendor: str = Field(default="all", description="Vendor filter")
    category: Optional[str] = Field(default=None, description="Category filter")
    reseller: Optional[str] = Field(default=None, description="Reseller filter")

    @field_validator('date_range')
    @classmethod
    def validate_date_range(cls, v: str) -> str:
        """Validate date range format."""
        valid_ranges = [
            "last_7_days", "last_14_days", "last_30_days",
            "last_60_days", "last_90_days", "last_180_days",
            "last_365_days", "this_month", "last_month",
            "this_quarter", "last_quarter", "this_year", "last_year",
            "all_time"
        ]
        if v not in valid_ranges:
            raise ValueError(f"Invalid date_range. Must be one of: {', '.join(valid_ranges)}")
        return v


# ============================================================
# Response Models
# ============================================================

class DashboardConfigResponse(BaseModel):
    """Dashboard configuration response model."""
    dashboard_id: UUID
    user_id: Optional[UUID]
    dashboard_name: str
    description: Optional[str]
    layout: List[WidgetConfig]
    kpis: List[KPIType]
    filters: DashboardFilters
    is_default: bool
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": None,
                "dashboard_name": "Overview Dashboard",
                "description": "Real-time overview of sales performance",
                "layout": [
                    {
                        "id": "kpi-grid",
                        "type": "kpi_grid",
                        "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                        "props": {"kpis": ["total_revenue", "total_units"]}
                    }
                ],
                "kpis": ["total_revenue", "total_units", "avg_price"],
                "filters": {"date_range": "last_30_days", "vendor": "all"},
                "is_default": True,
                "is_active": True,
                "display_order": 0,
                "created_at": "2025-10-10T10:00:00Z",
                "updated_at": "2025-10-10T10:00:00Z"
            }
        }
    }


# ============================================================
# Request Models
# ============================================================

class DashboardConfigCreate(BaseModel):
    """Request model for creating new dashboard configuration."""
    dashboard_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    layout: List[WidgetConfig] = Field(..., min_items=1)
    kpis: List[KPIType] = Field(default_factory=list)
    filters: DashboardFilters = Field(default_factory=DashboardFilters)
    is_default: bool = Field(default=False)
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0, ge=0)

    @field_validator('layout')
    @classmethod
    def validate_layout_unique_ids(cls, v: List[WidgetConfig]) -> List[WidgetConfig]:
        """Ensure all widget IDs are unique."""
        widget_ids = [widget.id for widget in v]
        if len(widget_ids) != len(set(widget_ids)):
            raise ValueError("All widget IDs must be unique within a dashboard")
        return v


class DashboardConfigUpdate(BaseModel):
    """Request model for updating dashboard configuration."""
    dashboard_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    layout: Optional[List[WidgetConfig]] = Field(default=None, min_items=1)
    kpis: Optional[List[KPIType]] = Field(default=None)
    filters: Optional[DashboardFilters] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = Field(default=None, ge=0)

    @field_validator('layout')
    @classmethod
    def validate_layout_unique_ids(cls, v: Optional[List[WidgetConfig]]) -> Optional[List[WidgetConfig]]:
        """Ensure all widget IDs are unique."""
        if v is not None:
            widget_ids = [widget.id for widget in v]
            if len(widget_ids) != len(set(widget_ids)):
                raise ValueError("All widget IDs must be unique within a dashboard")
        return v


# ============================================================
# List/Summary Models
# ============================================================

class DashboardConfigSummary(BaseModel):
    """Lightweight dashboard configuration summary (for lists)."""
    dashboard_id: UUID
    dashboard_name: str
    description: Optional[str]
    is_default: bool
    is_active: bool
    display_order: int
    widget_count: int
    kpi_count: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardConfigListResponse(BaseModel):
    """Response model for list of dashboard configurations."""
    dashboards: List[DashboardConfigSummary]
    total: int
    has_default: bool

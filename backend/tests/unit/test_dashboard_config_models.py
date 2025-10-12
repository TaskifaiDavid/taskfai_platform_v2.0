"""
Unit Tests for Dashboard Configuration Pydantic Models
Test T021: Validate Pydantic model validation rules
"""

import pytest
from pydantic import ValidationError

from app.models.dashboard_config import (
    WidgetPosition,
    WidgetConfig,
    DashboardFilters,
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigResponse,
    KPIType,
    WidgetType
)


class TestWidgetPosition:
    """Unit tests for WidgetPosition model"""

    def test_valid_widget_position(self):
        """Test valid widget position creation"""
        position = WidgetPosition(
            row=0,
            col=0,
            width=12,
            height=2
        )

        assert position.row == 0
        assert position.col == 0
        assert position.width == 12
        assert position.height == 2

    def test_widget_position_row_minimum(self):
        """Test row must be >= 0"""
        # Valid: row = 0
        position = WidgetPosition(row=0, col=0, width=12, height=2)
        assert position.row == 0

        # Invalid: row < 0
        with pytest.raises(ValidationError) as exc_info:
            WidgetPosition(row=-1, col=0, width=12, height=2)

        assert "row" in str(exc_info.value).lower()

    def test_widget_position_col_range(self):
        """Test col must be 0-11 (12-column grid)"""
        # Valid: col = 0
        position = WidgetPosition(row=0, col=0, width=12, height=2)
        assert position.col == 0

        # Valid: col = 11 (last column)
        position = WidgetPosition(row=0, col=11, width=1, height=2)
        assert position.col == 11

        # Invalid: col > 11
        with pytest.raises(ValidationError) as exc_info:
            WidgetPosition(row=0, col=12, width=12, height=2)

        assert "col" in str(exc_info.value).lower()

    def test_widget_position_width_range(self):
        """Test width must be 1-12"""
        # Valid: width = 1 (minimum)
        position = WidgetPosition(row=0, col=0, width=1, height=2)
        assert position.width == 1

        # Valid: width = 12 (maximum)
        position = WidgetPosition(row=0, col=0, width=12, height=2)
        assert position.width == 12

        # Invalid: width = 0
        with pytest.raises(ValidationError) as exc_info:
            WidgetPosition(row=0, col=0, width=0, height=2)

        assert "width" in str(exc_info.value).lower()

        # Invalid: width > 12
        with pytest.raises(ValidationError) as exc_info:
            WidgetPosition(row=0, col=0, width=13, height=2)

        assert "width" in str(exc_info.value).lower()

    def test_widget_position_height_minimum(self):
        """Test height must be >= 1"""
        # Valid: height = 1
        position = WidgetPosition(row=0, col=0, width=12, height=1)
        assert position.height == 1

        # Invalid: height = 0
        with pytest.raises(ValidationError) as exc_info:
            WidgetPosition(row=0, col=0, width=12, height=0)

        assert "height" in str(exc_info.value).lower()


class TestWidgetConfig:
    """Unit tests for WidgetConfig model"""

    def test_valid_widget_config(self):
        """Test valid widget configuration"""
        widget = WidgetConfig(
            id="kpi-grid-1",
            type=WidgetType.KPI_GRID,
            position=WidgetPosition(row=0, col=0, width=12, height=2),
            props={"kpis": ["total_revenue", "total_units"]}
        )

        assert widget.id == "kpi-grid-1"
        assert widget.type == WidgetType.KPI_GRID
        assert widget.position.width == 12
        assert widget.props["kpis"] == ["total_revenue", "total_units"]

    def test_widget_config_id_required(self):
        """Test widget id is required"""
        with pytest.raises(ValidationError) as exc_info:
            WidgetConfig(
                # Missing id
                type=WidgetType.KPI_GRID,
                position=WidgetPosition(row=0, col=0, width=12, height=2),
                props={}
            )

        assert "id" in str(exc_info.value).lower()

    def test_widget_config_empty_id_rejected(self):
        """Test empty widget id is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            WidgetConfig(
                id="",  # Empty string
                type=WidgetType.KPI_GRID,
                position=WidgetPosition(row=0, col=0, width=12, height=2),
                props={}
            )

        assert "id" in str(exc_info.value).lower()

    def test_widget_config_type_enum(self):
        """Test widget type must be valid enum"""
        # Valid types
        valid_types = [
            WidgetType.KPI_GRID,
            WidgetType.RECENT_UPLOADS,
            WidgetType.TOP_PRODUCTS,
            WidgetType.REVENUE_CHART,
            WidgetType.CATEGORY_REVENUE,
            WidgetType.RESELLER_PERFORMANCE,
            WidgetType.SALES_TREND
        ]

        for widget_type in valid_types:
            widget = WidgetConfig(
                id=f"widget-{widget_type.value}",
                type=widget_type,
                position=WidgetPosition(row=0, col=0, width=12, height=2),
                props={}
            )
            assert widget.type == widget_type

    def test_widget_config_props_default_empty_dict(self):
        """Test props defaults to empty dict"""
        widget = WidgetConfig(
            id="test",
            type=WidgetType.KPI_GRID,
            position=WidgetPosition(row=0, col=0, width=12, height=2),
            props={}
        )

        assert widget.props == {}


class TestDashboardFilters:
    """Unit tests for DashboardFilters model"""

    def test_valid_dashboard_filters(self):
        """Test valid dashboard filters"""
        filters = DashboardFilters(
            date_range="last_30_days",
            vendor="boxnox",
            category="electronics",
            reseller="Reseller A"
        )

        assert filters.date_range == "last_30_days"
        assert filters.vendor == "boxnox"
        assert filters.category == "electronics"
        assert filters.reseller == "Reseller A"

    def test_dashboard_filters_defaults(self):
        """Test default filter values"""
        filters = DashboardFilters()

        assert filters.date_range == "last_30_days"
        assert filters.vendor == "all"
        assert filters.category is None
        assert filters.reseller is None


class TestDashboardConfigCreate:
    """Unit tests for DashboardConfigCreate model"""

    def test_valid_dashboard_config_create(self):
        """Test valid dashboard config creation"""
        config = DashboardConfigCreate(
            dashboard_name="Test Dashboard",
            description="Test description",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={"kpis": ["total_revenue"]}
                )
            ],
            kpis=[KPIType.TOTAL_REVENUE, KPIType.TOTAL_UNITS],
            filters=DashboardFilters(),
            is_default=False,
            is_active=True,
            display_order=0
        )

        assert config.dashboard_name == "Test Dashboard"
        assert len(config.layout) == 1
        assert len(config.kpis) == 2

    def test_dashboard_name_required(self):
        """Test dashboard_name is required"""
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigCreate(
                # Missing dashboard_name
                layout=[
                    WidgetConfig(
                        id="widget-1",
                        type=WidgetType.KPI_GRID,
                        position=WidgetPosition(row=0, col=0, width=12, height=2),
                        props={}
                    )
                ]
            )

        assert "dashboard_name" in str(exc_info.value).lower()

    def test_dashboard_name_min_length(self):
        """Test dashboard_name minimum length = 1"""
        # Valid: 1 character
        config = DashboardConfigCreate(
            dashboard_name="A",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )
        assert config.dashboard_name == "A"

        # Invalid: empty string
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigCreate(
                dashboard_name="",
                layout=[
                    WidgetConfig(
                        id="widget-1",
                        type=WidgetType.KPI_GRID,
                        position=WidgetPosition(row=0, col=0, width=12, height=2),
                        props={}
                    )
                ]
            )

        assert "dashboard_name" in str(exc_info.value).lower()

    def test_dashboard_name_max_length(self):
        """Test dashboard_name maximum length = 255"""
        # Valid: 255 characters
        long_name = "A" * 255
        config = DashboardConfigCreate(
            dashboard_name=long_name,
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )
        assert len(config.dashboard_name) == 255

        # Invalid: 256 characters
        too_long_name = "A" * 256
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigCreate(
                dashboard_name=too_long_name,
                layout=[
                    WidgetConfig(
                        id="widget-1",
                        type=WidgetType.KPI_GRID,
                        position=WidgetPosition(row=0, col=0, width=12, height=2),
                        props={}
                    )
                ]
            )

        assert "dashboard_name" in str(exc_info.value).lower()

    def test_layout_required(self):
        """Test layout is required"""
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigCreate(
                dashboard_name="Test"
                # Missing layout
            )

        assert "layout" in str(exc_info.value).lower()

    def test_layout_min_items(self):
        """Test layout must have at least 1 widget"""
        # Valid: 1 widget
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )
        assert len(config.layout) == 1

        # Invalid: empty array
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigCreate(
                dashboard_name="Test",
                layout=[]
            )

        assert "layout" in str(exc_info.value).lower()

    def test_layout_unique_widget_ids(self):
        """Test widget IDs must be unique within layout"""
        # Valid: unique IDs
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                ),
                WidgetConfig(
                    id="widget-2",
                    type=WidgetType.RECENT_UPLOADS,
                    position=WidgetPosition(row=2, col=0, width=12, height=3),
                    props={}
                )
            ]
        )
        assert len(config.layout) == 2

        # Invalid: duplicate IDs
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigCreate(
                dashboard_name="Test",
                layout=[
                    WidgetConfig(
                        id="duplicate-id",
                        type=WidgetType.KPI_GRID,
                        position=WidgetPosition(row=0, col=0, width=12, height=2),
                        props={}
                    ),
                    WidgetConfig(
                        id="duplicate-id",  # Duplicate!
                        type=WidgetType.RECENT_UPLOADS,
                        position=WidgetPosition(row=2, col=0, width=12, height=3),
                        props={}
                    )
                ]
            )

        error_msg = str(exc_info.value).lower()
        assert "unique" in error_msg or "duplicate" in error_msg

    def test_kpis_default_empty_list(self):
        """Test kpis defaults to empty list"""
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )

        assert config.kpis == []

    def test_filters_default_empty_dict(self):
        """Test filters defaults to DashboardFilters()"""
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )

        assert isinstance(config.filters, DashboardFilters)
        assert config.filters.date_range == "last_30_days"

    def test_is_default_default_false(self):
        """Test is_default defaults to False"""
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )

        assert config.is_default is False

    def test_is_active_default_true(self):
        """Test is_active defaults to True"""
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )

        assert config.is_active is True

    def test_display_order_default_zero(self):
        """Test display_order defaults to 0"""
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ]
        )

        assert config.display_order == 0

    def test_display_order_non_negative(self):
        """Test display_order must be >= 0"""
        # Valid: 0
        config = DashboardConfigCreate(
            dashboard_name="Test",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ],
            display_order=0
        )
        assert config.display_order == 0

        # Invalid: negative
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigCreate(
                dashboard_name="Test",
                layout=[
                    WidgetConfig(
                        id="widget-1",
                        type=WidgetType.KPI_GRID,
                        position=WidgetPosition(row=0, col=0, width=12, height=2),
                        props={}
                    )
                ],
                display_order=-1
            )

        assert "display_order" in str(exc_info.value).lower()


class TestDashboardConfigUpdate:
    """Unit tests for DashboardConfigUpdate model"""

    def test_all_fields_optional(self):
        """Test all fields are optional in update model"""
        # Valid: empty update (no fields)
        update = DashboardConfigUpdate()

        # Should not raise error
        assert update.model_dump(exclude_unset=True) == {}

    def test_partial_update_dashboard_name(self):
        """Test updating only dashboard_name"""
        update = DashboardConfigUpdate(
            dashboard_name="Updated Name"
        )

        assert update.dashboard_name == "Updated Name"
        assert update.layout is None
        assert update.kpis is None

    def test_partial_update_layout(self):
        """Test updating only layout"""
        update = DashboardConfigUpdate(
            layout=[
                WidgetConfig(
                    id="new-widget",
                    type=WidgetType.TOP_PRODUCTS,
                    position=WidgetPosition(row=0, col=0, width=12, height=3),
                    props={}
                )
            ]
        )

        assert len(update.layout) == 1
        assert update.dashboard_name is None

    def test_update_empty_layout_rejected(self):
        """Test updating with empty layout is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            DashboardConfigUpdate(
                layout=[]
            )

        assert "layout" in str(exc_info.value).lower()

    def test_update_respects_validation_rules(self):
        """Test update model respects same validation as create"""
        # Invalid dashboard name
        with pytest.raises(ValidationError):
            DashboardConfigUpdate(
                dashboard_name=""  # Empty string
            )

        # Invalid display_order
        with pytest.raises(ValidationError):
            DashboardConfigUpdate(
                display_order=-1  # Negative
            )


class TestDashboardConfigResponse:
    """Unit tests for DashboardConfigResponse model"""

    def test_valid_dashboard_config_response(self):
        """Test valid response model"""
        from datetime import datetime

        response = DashboardConfigResponse(
            dashboard_id="550e8400-e29b-41d4-a716-446655440000",
            user_id="123e4567-e89b-12d3-a456-426614174000",
            dashboard_name="Test Dashboard",
            description="Test description",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ],
            kpis=[KPIType.TOTAL_REVENUE],
            filters=DashboardFilters(),
            is_default=True,
            is_active=True,
            display_order=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        assert response.dashboard_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.user_id == "123e4567-e89b-12d3-a456-426614174000"

    def test_response_user_id_nullable(self):
        """Test user_id can be None (tenant defaults)"""
        from datetime import datetime

        response = DashboardConfigResponse(
            dashboard_id="550e8400-e29b-41d4-a716-446655440000",
            user_id=None,  # Tenant default
            dashboard_name="Tenant Default",
            layout=[
                WidgetConfig(
                    id="widget-1",
                    type=WidgetType.KPI_GRID,
                    position=WidgetPosition(row=0, col=0, width=12, height=2),
                    props={}
                )
            ],
            kpis=[],
            filters=DashboardFilters(),
            is_default=True,
            is_active=True,
            display_order=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        assert response.user_id is None


class TestKPITypeEnum:
    """Unit tests for KPIType enum"""

    def test_kpi_type_values(self):
        """Test all KPI type enum values"""
        assert KPIType.TOTAL_REVENUE.value == "total_revenue"
        assert KPIType.TOTAL_UNITS.value == "total_units"
        assert KPIType.AVG_PRICE.value == "avg_price"
        assert KPIType.TOTAL_UPLOADS.value == "total_uploads"
        assert KPIType.RESELLER_COUNT.value == "reseller_count"
        assert KPIType.CATEGORY_MIX.value == "category_mix"
        assert KPIType.YOY_GROWTH.value == "yoy_growth"
        assert KPIType.TOP_PRODUCTS.value == "top_products"


class TestWidgetTypeEnum:
    """Unit tests for WidgetType enum"""

    def test_widget_type_values(self):
        """Test all widget type enum values"""
        assert WidgetType.KPI_GRID.value == "kpi_grid"
        assert WidgetType.RECENT_UPLOADS.value == "recent_uploads"
        assert WidgetType.TOP_PRODUCTS.value == "top_products"
        assert WidgetType.RESELLER_PERFORMANCE.value == "reseller_performance"
        assert WidgetType.CATEGORY_REVENUE.value == "category_revenue"
        assert WidgetType.REVENUE_CHART.value == "revenue_chart"
        assert WidgetType.SALES_TREND.value == "sales_trend"

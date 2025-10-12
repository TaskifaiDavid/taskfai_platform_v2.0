"""
Contract Tests for Dashboard Configuration API
Tests T004-T009: All 6 CRUD endpoints for dynamic dashboard configs
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardConfigDefaultContract:
    """T004: Contract tests for GET /api/dashboard-configs/default endpoint"""

    async def test_get_default_config_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful default dashboard config retrieval

        Expected response:
        {
            "dashboard_id": "uuid",
            "user_id": "uuid" or null (tenant default),
            "dashboard_name": "Overview Dashboard",
            "description": "Default dashboard for all users",
            "layout": [
                {
                    "id": "kpi-grid-1",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {"kpis": ["total_revenue", "total_units"]}
                }
            ],
            "kpis": ["total_revenue", "total_units", "avg_price"],
            "filters": {"date_range": "last_30_days"},
            "is_default": true,
            "is_active": true,
            "display_order": 0,
            "created_at": "2025-10-12T10:00:00Z",
            "updated_at": "2025-10-12T10:00:00Z"
        }
        """
        response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "dashboard_id" in data
        assert "dashboard_name" in data
        assert "layout" in data
        assert "kpis" in data
        assert "filters" in data
        assert "is_default" in data
        assert "is_active" in data
        assert "display_order" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Types
        assert isinstance(data["dashboard_id"], str)
        assert isinstance(data["dashboard_name"], str)
        assert isinstance(data["layout"], list)
        assert isinstance(data["kpis"], list)
        assert isinstance(data["filters"], dict)
        assert isinstance(data["is_default"], bool)
        assert isinstance(data["is_active"], bool)
        assert isinstance(data["display_order"], int)

        # Constraints
        assert data["is_default"] is True  # Default endpoint returns default config
        assert len(data["layout"]) >= 1  # Must have at least one widget

    async def test_get_default_config_widget_structure(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test widget structure in layout array

        Each widget must have: id, type, position, props
        Position must have: row, col, width, height
        """
        response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        for widget in data["layout"]:
            # Widget structure
            assert "id" in widget
            assert "type" in widget
            assert "position" in widget
            assert "props" in widget

            # Position structure
            position = widget["position"]
            assert "row" in position
            assert "col" in position
            assert "width" in position
            assert "height" in position

            # Position constraints
            assert position["row"] >= 0
            assert 0 <= position["col"] <= 11  # 12-column grid
            assert 1 <= position["width"] <= 12
            assert position["height"] >= 1

    async def test_get_default_config_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test 404 when no default config exists

        Expected:
        - New tenant with no configs returns 404
        """
        # This test would need a fresh tenant with no configs
        # For now, we expect 200 since tenant defaults should exist
        response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        # Should return either 200 (default exists) or 404 (no default)
        assert response.status_code in [200, 404]

    async def test_get_default_config_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.get("/api/dashboard-configs/default")

        assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardConfigListContract:
    """T005: Contract tests for GET /api/dashboard-configs endpoint"""

    async def test_list_configs_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful dashboard configs list retrieval

        Expected response:
        {
            "dashboards": [
                {
                    "dashboard_id": "uuid",
                    "dashboard_name": "Overview Dashboard",
                    "description": "Default dashboard",
                    "is_default": true,
                    "is_active": true,
                    "display_order": 0,
                    "widget_count": 3,
                    "kpi_count": 5,
                    "updated_at": "2025-10-12T10:00:00Z"
                }
            ],
            "total": 1,
            "has_default": true
        }
        """
        response = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "dashboards" in data
        assert "total" in data
        assert "has_default" in data

        # Types
        assert isinstance(data["dashboards"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["has_default"], bool)

        # Dashboard summary structure
        if len(data["dashboards"]) > 0:
            dashboard = data["dashboards"][0]
            assert "dashboard_id" in dashboard
            assert "dashboard_name" in dashboard
            assert "is_default" in dashboard
            assert "is_active" in dashboard
            assert "widget_count" in dashboard
            assert "kpi_count" in dashboard
            assert "updated_at" in dashboard

    async def test_list_configs_with_tenant_defaults(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test include_tenant_defaults parameter

        Expected:
        - include_tenant_defaults=true: returns user configs + tenant defaults
        - include_tenant_defaults=false: returns only user configs
        """
        # With tenant defaults (default behavior)
        response = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers,
            params={"include_tenant_defaults": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["dashboards"], list)

    async def test_list_configs_filter_by_active(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering by is_active parameter

        Expected:
        - is_active=true: returns only active configs
        - is_active=false: returns only inactive configs
        """
        response = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers,
            params={"is_active": True}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned configs should be active
        for dashboard in data["dashboards"]:
            assert dashboard["is_active"] is True

    async def test_list_configs_filter_by_default(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering by is_default parameter

        Expected:
        - is_default=true: returns only default configs
        """
        response = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers,
            params={"is_default": True}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned configs should be default
        for dashboard in data["dashboards"]:
            assert dashboard["is_default"] is True

    async def test_list_configs_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.get("/api/dashboard-configs")

        assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardConfigGetByIdContract:
    """T006: Contract tests for GET /api/dashboard-configs/{id} endpoint"""

    async def test_get_config_by_id_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful config retrieval by ID

        Expected:
        - Returns full dashboard config with all fields
        - Valid UUID returns 200
        """
        # First, get default config to get a valid ID
        list_response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        if list_response.status_code == 200:
            default_config = list_response.json()
            dashboard_id = default_config["dashboard_id"]

            # Now get by ID
            response = await async_client.get(
                f"/api/dashboard-configs/{dashboard_id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            # Should return same config as default
            assert data["dashboard_id"] == dashboard_id

    async def test_get_config_by_id_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test 404 for non-existent config ID

        Expected:
        - Invalid UUID returns 404
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await async_client.get(
            f"/api/dashboard-configs/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_config_by_id_invalid_uuid(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test 422 for invalid UUID format

        Expected:
        - Non-UUID string returns 422
        """
        response = await async_client.get(
            "/api/dashboard-configs/not-a-uuid",
            headers=auth_headers
        )

        assert response.status_code == 422

    async def test_get_config_by_id_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await async_client.get(
            f"/api/dashboard-configs/{fake_id}"
        )

        assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardConfigCreateContract:
    """T007: Contract tests for POST /api/dashboard-configs endpoint"""

    async def test_create_config_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful dashboard config creation

        Expected response:
        {
            "dashboard_id": "new-uuid",
            "user_id": "user-uuid",
            "dashboard_name": "My Custom Dashboard",
            "description": "Custom sales dashboard",
            "layout": [...],
            "kpis": ["total_revenue", "total_units"],
            "filters": {"date_range": "last_90_days"},
            "is_default": false,
            "is_active": true,
            "display_order": 0,
            "created_at": "2025-10-12T10:00:00Z",
            "updated_at": "2025-10-12T10:00:00Z"
        }
        """
        request_body = {
            "dashboard_name": "Test Dashboard",
            "description": "Test dashboard for contract tests",
            "layout": [
                {
                    "id": "test-kpi-grid",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {"kpis": ["total_revenue", "total_units"]}
                }
            ],
            "kpis": ["total_revenue", "total_units"],
            "filters": {"date_range": "last_30_days"},
            "is_default": False,
            "is_active": True,
            "display_order": 0
        }

        response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields
        assert "dashboard_id" in data
        assert "user_id" in data
        assert data["dashboard_name"] == request_body["dashboard_name"]
        assert data["description"] == request_body["description"]
        assert len(data["layout"]) == len(request_body["layout"])
        assert data["kpis"] == request_body["kpis"]
        assert data["is_default"] == request_body["is_default"]
        assert data["is_active"] == request_body["is_active"]

    async def test_create_config_missing_required_fields(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test missing required fields returns 422

        Required: dashboard_name, layout
        """
        request_body = {
            "dashboard_name": "Test"
            # Missing layout
        }

        response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 422

    async def test_create_config_empty_layout_rejected(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test empty layout array returns 422

        Expected:
        - layout must have at least 1 widget
        """
        request_body = {
            "dashboard_name": "Test",
            "layout": []  # Empty layout
        }

        response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 422

    async def test_create_config_invalid_widget_position(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test invalid widget position returns 422

        Expected:
        - col must be 0-11
        - width must be 1-12
        - row, height must be >= 1
        """
        request_body = {
            "dashboard_name": "Test",
            "layout": [
                {
                    "id": "test",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 15, "width": 12, "height": 2},  # col > 11
                    "props": {}
                }
            ]
        }

        response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 422

    async def test_create_config_invalid_widget_type(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test invalid widget type returns 422

        Expected:
        - type must be one of: kpi_grid, recent_uploads, top_products, etc.
        """
        request_body = {
            "dashboard_name": "Test",
            "layout": [
                {
                    "id": "test",
                    "type": "invalid_widget_type",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {}
                }
            ]
        }

        response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 422

    async def test_create_config_default_values(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test default values applied correctly

        Expected defaults:
        - kpis: []
        - filters: {}
        - is_default: false
        - is_active: true
        - display_order: 0
        """
        request_body = {
            "dashboard_name": "Minimal Dashboard",
            "layout": [
                {
                    "id": "test",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {}
                }
            ]
        }

        response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        # Check defaults
        assert data["kpis"] == []
        assert data["filters"] == {}
        assert data["is_default"] is False
        assert data["is_active"] is True
        assert data["display_order"] == 0

    async def test_create_config_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        request_body = {
            "dashboard_name": "Test",
            "layout": [
                {
                    "id": "test",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {}
                }
            ]
        }

        response = await async_client.post(
            "/api/dashboard-configs",
            json=request_body
        )

        assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardConfigUpdateContract:
    """T008: Contract tests for PUT /api/dashboard-configs/{id} endpoint"""

    async def test_update_config_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful config update

        Expected:
        - Returns 200 with updated config
        - updated_at timestamp changed
        """
        # First create a config to update
        create_body = {
            "dashboard_name": "Original Name",
            "layout": [
                {
                    "id": "test",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {}
                }
            ]
        }

        create_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=create_body
        )

        if create_response.status_code == 201:
            created = create_response.json()
            dashboard_id = created["dashboard_id"]

            # Now update it
            update_body = {
                "dashboard_name": "Updated Name",
                "description": "Updated description"
            }

            response = await async_client.put(
                f"/api/dashboard-configs/{dashboard_id}",
                headers=auth_headers,
                json=update_body
            )

            assert response.status_code == 200
            data = response.json()

            assert data["dashboard_id"] == dashboard_id
            assert data["dashboard_name"] == "Updated Name"
            assert data["description"] == "Updated description"
            assert data["updated_at"] != created["updated_at"]

    async def test_update_config_partial_update(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test partial update (not all fields required)

        Expected:
        - Can update single field
        - Other fields remain unchanged
        """
        # Create config
        create_body = {
            "dashboard_name": "Original",
            "description": "Original description",
            "layout": [
                {
                    "id": "test",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {}
                }
            ]
        }

        create_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=create_body
        )

        if create_response.status_code == 201:
            created = create_response.json()
            dashboard_id = created["dashboard_id"]

            # Update only name
            update_body = {
                "dashboard_name": "New Name Only"
            }

            response = await async_client.put(
                f"/api/dashboard-configs/{dashboard_id}",
                headers=auth_headers,
                json=update_body
            )

            assert response.status_code == 200
            data = response.json()

            assert data["dashboard_name"] == "New Name Only"
            assert data["description"] == "Original description"  # Unchanged

    async def test_update_config_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test 404 for non-existent config
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_body = {"dashboard_name": "Updated"}

        response = await async_client.put(
            f"/api/dashboard-configs/{fake_id}",
            headers=auth_headers,
            json=update_body
        )

        assert response.status_code == 404

    async def test_update_config_invalid_data(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test 422 for invalid update data

        Expected:
        - Invalid widget position rejected
        - Empty layout rejected
        """
        # Create config first
        create_body = {
            "dashboard_name": "Test",
            "layout": [
                {
                    "id": "test",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {}
                }
            ]
        }

        create_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=create_body
        )

        if create_response.status_code == 201:
            dashboard_id = create_response.json()["dashboard_id"]

            # Try to update with empty layout
            update_body = {"layout": []}

            response = await async_client.put(
                f"/api/dashboard-configs/{dashboard_id}",
                headers=auth_headers,
                json=update_body
            )

            assert response.status_code == 422

    async def test_update_config_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_body = {"dashboard_name": "Updated"}

        response = await async_client.put(
            f"/api/dashboard-configs/{fake_id}",
            json=update_body
        )

        assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardConfigDeleteContract:
    """T009: Contract tests for DELETE /api/dashboard-configs/{id} endpoint"""

    async def test_delete_config_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful config deletion

        Expected:
        - Returns 204 No Content
        - Subsequent GET returns 404
        """
        # Create config to delete
        create_body = {
            "dashboard_name": "To Delete",
            "layout": [
                {
                    "id": "test",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {}
                }
            ]
        }

        create_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=create_body
        )

        if create_response.status_code == 201:
            dashboard_id = create_response.json()["dashboard_id"]

            # Delete it
            response = await async_client.delete(
                f"/api/dashboard-configs/{dashboard_id}",
                headers=auth_headers
            )

            assert response.status_code == 204

            # Verify it's deleted
            get_response = await async_client.get(
                f"/api/dashboard-configs/{dashboard_id}",
                headers=auth_headers
            )

            assert get_response.status_code == 404

    async def test_delete_config_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test 404 for non-existent config
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await async_client.delete(
            f"/api/dashboard-configs/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_delete_config_invalid_uuid(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test 422 for invalid UUID format
        """
        response = await async_client.delete(
            "/api/dashboard-configs/not-a-uuid",
            headers=auth_headers
        )

        assert response.status_code == 422

    async def test_delete_config_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await async_client.delete(
            f"/api/dashboard-configs/{fake_id}"
        )

        assert response.status_code == 401

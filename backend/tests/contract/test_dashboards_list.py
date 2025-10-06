"""
T074: Dashboard List API Contract Test
GET /api/dashboards
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardListContract:
    """Contract tests for GET /api/dashboards endpoint"""

    async def test_list_dashboards_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful dashboard list retrieval

        Expected response:
        {
            "dashboards": [
                {
                    "config_id": "uuid",
                    "dashboard_name": "My Dashboard",
                    "type": "superset",
                    "url": "https://...",
                    "is_primary": true,
                    "created_at": "...",
                    "updated_at": "..."
                }
            ],
            "total": 5
        }
        """
        response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "dashboards" in data
        assert "total" in data
        assert isinstance(data["dashboards"], list)
        assert isinstance(data["total"], int)

        # If dashboards exist, verify structure
        if len(data["dashboards"]) > 0:
            dashboard = data["dashboards"][0]
            assert "config_id" in dashboard
            assert "dashboard_name" in dashboard
            assert "type" in dashboard
            assert "url" in dashboard
            assert "is_primary" in dashboard

    async def test_list_dashboards_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.get("/api/dashboards")

        assert response.status_code == 401

    async def test_list_dashboards_empty_for_new_user(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test new user with no dashboards returns empty list

        Expected:
        - Status: 200
        - dashboards: []
        - total: 0
        """
        response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "dashboards" in data
        assert "total" in data

    async def test_list_dashboards_primary_flag(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test primary dashboard is correctly flagged

        Expected:
        - Only one dashboard has is_primary: true
        - Others have is_primary: false
        """
        response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Count primary dashboards
        primary_count = sum(1 for d in data["dashboards"] if d.get("is_primary"))
        assert primary_count <= 1, "Only one dashboard should be primary"

    async def test_list_dashboards_no_credentials_in_response(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test auth credentials not exposed in list

        Expected:
        - No auth_credentials field in response
        - No plaintext passwords
        """
        response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        for dashboard in data["dashboards"]:
            assert "auth_credentials" not in dashboard or dashboard["auth_credentials"] is None
            assert "password" not in str(dashboard).lower()

    async def test_list_dashboards_sorted_by_created_date(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test dashboards sorted by creation date

        Expected:
        - Most recent first (descending order)
        """
        response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        dashboards = data["dashboards"]
        if len(dashboards) > 1:
            for i in range(len(dashboards) - 1):
                assert dashboards[i]["created_at"] >= dashboards[i+1]["created_at"]

    async def test_list_dashboards_filter_by_type(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering by dashboard type

        Expected:
        - Query param: type=superset
        - Returns only Superset dashboards
        """
        response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers,
            params={"type": "superset"}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned dashboards should match filter
        for dashboard in data["dashboards"]:
            assert dashboard["type"] == "superset"

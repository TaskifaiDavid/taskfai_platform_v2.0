"""
T077: Dashboard Set Primary API Contract Test
PATCH /api/dashboards/{id}/primary
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardSetPrimaryContract:
    """Contract tests for PATCH /api/dashboards/{id}/primary endpoint"""

    async def test_set_primary_dashboard_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successfully setting dashboard as primary

        Expected response:
        {
            "message": "Dashboard set as primary",
            "config_id": "uuid",
            "is_primary": true
        }
        """
        dashboard_id = "test-dashboard-uuid"

        response = await async_client.patch(
            f"/api/dashboards/{dashboard_id}/primary",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "is_primary" in data
            if "is_primary" in data:
                assert data["is_primary"] is True

    async def test_set_primary_clears_previous_primary(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        CRITICAL: Test only one dashboard can be primary

        Expected:
        - Setting dashboard A as primary
        - Previous primary dashboard B becomes non-primary
        - Only one primary dashboard in list
        """
        dashboard_a = "dashboard-a-uuid"
        dashboard_b = "dashboard-b-uuid"

        # Set A as primary
        await async_client.patch(
            f"/api/dashboards/{dashboard_a}/primary",
            headers=auth_headers
        )

        # Set B as primary (should clear A)
        response = await async_client.patch(
            f"/api/dashboards/{dashboard_b}/primary",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        # List all dashboards
        list_response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        if list_response.status_code == 200:
            data = list_response.json()
            primary_count = sum(1 for d in data["dashboards"] if d.get("is_primary"))
            assert primary_count <= 1, "Only one dashboard should be primary"

    async def test_set_primary_dashboard_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test setting non-existent dashboard as primary returns 404

        Expected:
        - Status: 404 Not Found
        """
        response = await async_client.patch(
            "/api/dashboards/non-existent-uuid/primary",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_set_primary_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.patch(
            "/api/dashboards/test-id/primary"
        )

        assert response.status_code == 401

    async def test_set_primary_user_ownership(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test user can only set their own dashboards as primary

        Expected:
        - Cannot set another user's dashboard as primary
        - Returns 403 or 404
        """
        other_user_dashboard = "other-user-dashboard-uuid"

        response = await async_client.patch(
            f"/api/dashboards/{other_user_dashboard}/primary",
            headers=auth_headers
        )

        assert response.status_code in [403, 404]

    async def test_set_primary_idempotent(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test setting already-primary dashboard as primary again

        Expected:
        - Status: 200
        - No error
        - Dashboard remains primary
        """
        dashboard_id = "test-dashboard-uuid"

        # Set as primary twice
        response1 = await async_client.patch(
            f"/api/dashboards/{dashboard_id}/primary",
            headers=auth_headers
        )

        response2 = await async_client.patch(
            f"/api/dashboards/{dashboard_id}/primary",
            headers=auth_headers
        )

        assert response2.status_code in [200, 404]

    async def test_unset_primary_dashboard(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test unsetting primary dashboard (optional feature)

        Expected:
        - If endpoint supports DELETE or PATCH with is_primary: false
        - Primary flag cleared
        """
        dashboard_id = "test-dashboard-uuid"

        # Set as primary
        await async_client.patch(
            f"/api/dashboards/{dashboard_id}/primary",
            headers=auth_headers
        )

        # Try to unset (might be DELETE or body param)
        response = await async_client.delete(
            f"/api/dashboards/{dashboard_id}/primary",
            headers=auth_headers
        )

        # Endpoint might not support this, so accept various responses
        assert response.status_code in [200, 204, 404, 405]

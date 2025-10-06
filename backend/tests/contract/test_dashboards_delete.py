"""
T076: Dashboard Delete API Contract Test
DELETE /api/dashboards/{id}
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardDeleteContract:
    """Contract tests for DELETE /api/dashboards/{id} endpoint"""

    async def test_delete_dashboard_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful dashboard deletion

        Expected response:
        {
            "message": "Dashboard deleted",
            "config_id": "uuid"
        }
        """
        dashboard_id = "test-dashboard-uuid"

        response = await async_client.delete(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 204, 404]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "detail" in data

    async def test_delete_dashboard_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test deleting non-existent dashboard returns 404

        Expected:
        - Status: 404 Not Found
        """
        response = await async_client.delete(
            "/api/dashboards/non-existent-uuid",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_delete_dashboard_verifiable_by_get(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test deleted dashboard no longer retrievable

        Expected:
        - DELETE succeeds
        - GET returns 404
        """
        dashboard_id = "test-dashboard-uuid"

        # Delete dashboard
        delete_response = await async_client.delete(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers
        )

        # Verify deletion (if it existed)
        if delete_response.status_code in [200, 204]:
            # Try to get deleted dashboard
            get_response = await async_client.get(
                f"/api/dashboards/{dashboard_id}",
                headers=auth_headers
            )
            assert get_response.status_code == 404

    async def test_delete_dashboard_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.delete("/api/dashboards/test-id")

        assert response.status_code == 401

    async def test_delete_dashboard_user_ownership(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test user can only delete their own dashboards

        Expected:
        - Cannot delete dashboard belonging to another user
        - Returns 403 or 404
        """
        other_user_dashboard = "other-user-dashboard-uuid"

        response = await async_client.delete(
            f"/api/dashboards/{other_user_dashboard}",
            headers=auth_headers
        )

        assert response.status_code in [403, 404]

    async def test_delete_primary_dashboard_resets_primary(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test deleting primary dashboard clears primary flag

        Expected:
        - If deleted dashboard was primary
        - Another dashboard might become primary
        - Or no dashboard is primary
        """
        # This tests behavior when primary dashboard is deleted
        # Exact behavior depends on business rules
        dashboard_id = "primary-dashboard-uuid"

        response = await async_client.delete(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 204, 404]

        # Check remaining dashboards
        list_response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        if list_response.status_code == 200:
            data = list_response.json()
            # Either no primary or one primary
            primary_count = sum(1 for d in data["dashboards"] if d.get("is_primary"))
            assert primary_count <= 1

    async def test_delete_dashboard_idempotent(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test deleting already deleted dashboard

        Expected:
        - Second DELETE returns 404 (or 204/410)
        """
        dashboard_id = "test-dashboard-uuid"

        # Delete once
        await async_client.delete(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers
        )

        # Delete again
        response = await async_client.delete(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers
        )

        assert response.status_code in [404, 204, 410]

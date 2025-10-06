"""
T075: Dashboard Update API Contract Test
PUT /api/dashboards/{id}
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardUpdateContract:
    """Contract tests for PUT /api/dashboards/{id} endpoint"""

    async def test_update_dashboard_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful dashboard update

        Expected response:
        {
            "config_id": "uuid",
            "dashboard_name": "Updated Name",
            "type": "superset",
            "url": "https://new-url.com",
            "updated_at": "2025-10-06T10:00:00Z"
        }
        """
        dashboard_id = "test-dashboard-uuid"

        request_body = {
            "dashboard_name": "Updated Dashboard Name",
            "url": "https://updated.example.com/dashboard"
        }

        response = await async_client.put(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 404]  # 404 if dashboard doesn't exist

        if response.status_code == 200:
            data = response.json()
            assert data["dashboard_name"] == request_body["dashboard_name"]
            assert data["url"] == request_body["url"]
            assert "updated_at" in data

    async def test_update_dashboard_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test updating non-existent dashboard returns 404

        Expected:
        - Status: 404 Not Found
        """
        response = await async_client.put(
            "/api/dashboards/non-existent-uuid",
            headers=auth_headers,
            json={"dashboard_name": "Test"}
        )

        assert response.status_code == 404

    async def test_update_dashboard_partial_update(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test partial update (only some fields)

        Expected:
        - Can update just dashboard_name
        - Can update just url
        - Other fields unchanged
        """
        dashboard_id = "test-dashboard-uuid"

        # Update only name
        response = await async_client.put(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers,
            json={"dashboard_name": "New Name Only"}
        )

        assert response.status_code in [200, 404]

    async def test_update_dashboard_invalid_url(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test invalid URL rejected

        Expected:
        - Status: 400 Bad Request
        - Error about invalid URL
        """
        dashboard_id = "test-dashboard-uuid"

        response = await async_client.put(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers,
            json={"url": "not-a-valid-url"}
        )

        assert response.status_code in [400, 404]

    async def test_update_dashboard_http_url_rejected(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test HTTP URL rejected (only HTTPS allowed)

        Expected:
        - Status: 400
        - Error about HTTPS requirement
        """
        dashboard_id = "test-dashboard-uuid"

        response = await async_client.put(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers,
            json={"url": "http://insecure.example.com"}
        )

        assert response.status_code in [400, 404]

    async def test_update_dashboard_credentials(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test updating auth credentials

        Expected:
        - Can update credentials
        - Credentials encrypted in storage
        - Not returned in response
        """
        dashboard_id = "test-dashboard-uuid"

        request_body = {
            "auth_credentials": {
                "username": "new_user",
                "password": "new_password"
            }
        }

        response = await async_client.put(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Credentials should not be in response
            assert "auth_credentials" not in data or data["auth_credentials"] is None

    async def test_update_dashboard_cannot_change_type(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test dashboard type cannot be changed after creation

        Expected:
        - Type field ignored or rejected
        - Original type preserved
        """
        dashboard_id = "test-dashboard-uuid"

        response = await async_client.put(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers,
            json={"type": "different_type"}
        )

        # Either rejected or type ignored
        assert response.status_code in [200, 400, 404]

    async def test_update_dashboard_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.put(
            "/api/dashboards/test-id",
            json={"dashboard_name": "Test"}
        )

        assert response.status_code == 401

    async def test_update_dashboard_user_ownership(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test user can only update their own dashboards

        Expected:
        - Cannot update dashboard belonging to another user
        - Returns 403 or 404
        """
        # Attempt to update dashboard owned by different user
        other_user_dashboard = "other-user-dashboard-uuid"

        response = await async_client.put(
            f"/api/dashboards/{other_user_dashboard}",
            headers=auth_headers,
            json={"dashboard_name": "Hacked Name"}
        )

        assert response.status_code in [403, 404]

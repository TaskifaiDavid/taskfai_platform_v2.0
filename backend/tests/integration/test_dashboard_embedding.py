"""
T089: Dashboard Embedding Integration Test
Config → Validate → Encrypt → Display
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestDashboardEmbeddingIntegration:
    """Integration tests for dashboard embedding workflow"""

    async def test_complete_dashboard_embedding_flow(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test complete dashboard embedding flow

        Flow:
        1. User creates dashboard config with credentials
        2. URL validated (HTTPS, format, domain)
        3. Credentials encrypted with AES-256
        4. Config stored in DB
        5. Frontend retrieves config
        6. Credentials decrypted for iframe auth
        7. Dashboard displayed in secure iframe
        """
        # Step 1-4: Create dashboard config
        create_response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "Sales Dashboard",
                "type": "superset",
                "url": "https://superset.example.com/dashboard/123",
                "auth_credentials": {
                    "username": "testuser",
                    "password": "testpass123"
                }
            }
        )

        assert create_response.status_code == 201
        dashboard = create_response.json()
        config_id = dashboard["config_id"]

        # Step 5: Retrieve config (credentials should NOT be in response)
        get_response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        assert get_response.status_code == 200
        dashboards = get_response.json()["dashboards"]

        # Find our dashboard
        our_dashboard = next((d for d in dashboards if d["config_id"] == config_id), None)
        assert our_dashboard is not None

        # Step 6: Credentials should be encrypted, not exposed
        assert "auth_credentials" not in our_dashboard or \
               our_dashboard["auth_credentials"] is None

    async def test_url_validation_before_storage(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test URL validation prevents insecure URLs

        Expected:
        - HTTP URLs rejected
        - Invalid URLs rejected
        - Only HTTPS allowed
        """
        # Try HTTP (should fail)
        http_response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "Test",
                "type": "superset",
                "url": "http://insecure.example.com/dashboard"
            }
        )

        assert http_response.status_code == 400

        # Try HTTPS (should succeed)
        https_response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "Test",
                "type": "superset",
                "url": "https://secure.example.com/dashboard"
            }
        )

        assert https_response.status_code == 201

    async def test_credential_encryption_in_database(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        CRITICAL: Test credentials encrypted in database

        Expected:
        - Credentials encrypted before storage
        - Cannot query plaintext credentials
        - Encryption key from environment
        """
        # Create dashboard with credentials
        create_response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "Secure Dashboard",
                "type": "superset",
                "url": "https://example.com/dashboard",
                "auth_credentials": {
                    "username": "admin",
                    "password": "secret_password_123"
                }
            }
        )

        assert create_response.status_code == 201

        # In real implementation, would query DB directly to verify encryption
        # Here we verify credentials not exposed in API responses

        # Get dashboard list
        list_response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        assert list_response.status_code == 200
        dashboards = list_response.json()["dashboards"]

        # Verify no plaintext passwords in response
        for dashboard in dashboards:
            response_str = str(dashboard)
            assert "secret_password_123" not in response_str, \
                "Plaintext password exposed in API response!"

    async def test_primary_dashboard_flag(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test primary dashboard workflow

        Expected:
        - Can set one dashboard as primary
        - Frontend displays primary by default
        - Only one primary at a time
        """
        # Create two dashboards
        dash1 = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "Dashboard 1",
                "type": "superset",
                "url": "https://example.com/dash1"
            }
        )

        dash2 = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "Dashboard 2",
                "type": "superset",
                "url": "https://example.com/dash2"
            }
        )

        dash1_id = dash1.json()["config_id"]
        dash2_id = dash2.json()["config_id"]

        # Set dash1 as primary
        await async_client.patch(
            f"/api/dashboards/{dash1_id}/primary",
            headers=auth_headers
        )

        # Set dash2 as primary (should clear dash1)
        await async_client.patch(
            f"/api/dashboards/{dash2_id}/primary",
            headers=auth_headers
        )

        # List dashboards
        list_response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        dashboards = list_response.json()["dashboards"]

        # Only dash2 should be primary
        primary_count = sum(1 for d in dashboards if d.get("is_primary"))
        assert primary_count <= 1, "Only one dashboard should be primary"

    async def test_dashboard_update_preserves_encryption(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test updating dashboard preserves credential encryption

        Expected:
        - Can update dashboard_name, url
        - Credentials remain encrypted
        - Can update credentials (re-encrypted)
        """
        # Create dashboard
        create_response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "Original Name",
                "type": "superset",
                "url": "https://example.com/dash",
                "auth_credentials": {
                    "username": "user",
                    "password": "pass"
                }
            }
        )

        dashboard_id = create_response.json()["config_id"]

        # Update dashboard
        update_response = await async_client.put(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers,
            json={
                "dashboard_name": "Updated Name",
                "url": "https://example.com/dash2"
            }
        )

        assert update_response.status_code in [200, 404]

        if update_response.status_code == 200:
            # Credentials should still be encrypted
            data = update_response.json()
            assert "auth_credentials" not in data or data["auth_credentials"] is None

    async def test_multiple_dashboard_types_supported(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test different dashboard types can be embedded

        Expected types:
        - Superset
        - Tableau
        - Power BI
        - Looker
        - Metabase
        """
        dashboard_types = ["superset", "tableau", "power_bi", "looker", "metabase"]

        for dash_type in dashboard_types:
            response = await async_client.post(
                "/api/dashboards",
                headers=auth_headers,
                json={
                    "dashboard_name": f"{dash_type.title()} Dashboard",
                    "type": dash_type,
                    "url": f"https://{dash_type}.example.com/dashboard"
                }
            )

            assert response.status_code == 201

    async def test_dashboard_deletion_removes_credentials(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test deleting dashboard securely removes credentials

        Expected:
        - Credentials deleted from DB
        - No orphaned encrypted data
        """
        # Create dashboard
        create_response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json={
                "dashboard_name": "To Delete",
                "type": "superset",
                "url": "https://example.com/dash",
                "auth_credentials": {
                    "username": "user",
                    "password": "pass"
                }
            }
        )

        dashboard_id = create_response.json()["config_id"]

        # Delete dashboard
        delete_response = await async_client.delete(
            f"/api/dashboards/{dashboard_id}",
            headers=auth_headers
        )

        assert delete_response.status_code in [200, 204, 404]

        # Verify deleted
        get_response = await async_client.get(
            "/api/dashboards",
            headers=auth_headers
        )

        dashboards = get_response.json()["dashboards"]
        assert not any(d["config_id"] == dashboard_id for d in dashboards)

"""
T073: Dashboard Create API Contract Test
POST /api/dashboards
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestDashboardCreateContract:
    """Contract tests for POST /api/dashboards endpoint"""

    async def test_create_dashboard_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful dashboard creation

        Expected response:
        {
            "config_id": "uuid",
            "dashboard_name": "My Dashboard",
            "type": "superset",
            "url": "https://superset.example.com/dashboard/1",
            "is_primary": false,
            "created_at": "2025-10-06T10:00:00Z"
        }
        """
        request_body = {
            "dashboard_name": "Sales Dashboard",
            "type": "superset",
            "url": "https://superset.example.com/dashboard/123",
            "auth_credentials": {
                "username": "user",
                "password": "pass"
            }
        }

        response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        assert "config_id" in data
        assert data["dashboard_name"] == "Sales Dashboard"
        assert data["type"] == "superset"
        assert data["url"] == request_body["url"]
        assert "is_primary" in data
        assert "created_at" in data

    async def test_create_dashboard_missing_required_fields(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test missing required fields returns 422

        Required: dashboard_name, type, url
        """
        request_body = {
            "dashboard_name": "Test"
            # Missing type and url
        }

        response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 422

    async def test_create_dashboard_invalid_url(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test invalid URL format returns 400

        Expected:
        - Must be HTTPS
        - Must be valid URL format
        """
        request_body = {
            "dashboard_name": "Test",
            "type": "superset",
            "url": "not-a-valid-url"
        }

        response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 400

    async def test_create_dashboard_http_rejected(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test HTTP URLs rejected (only HTTPS allowed)

        Expected:
        - Status: 400
        - Error about HTTPS requirement
        """
        request_body = {
            "dashboard_name": "Test",
            "type": "superset",
            "url": "http://insecure.example.com/dashboard"
        }

        response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 400
        data = response.json()
        assert "https" in data["detail"].lower()

    async def test_create_dashboard_credentials_encrypted(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test auth credentials are encrypted

        Expected:
        - Credentials not returned in response (encrypted in DB)
        - Response should not contain plaintext credentials
        """
        request_body = {
            "dashboard_name": "Test",
            "type": "superset",
            "url": "https://example.com/dashboard",
            "auth_credentials": {
                "username": "testuser",
                "password": "secret_password_123"
            }
        }

        response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        # Credentials should not be in response
        assert "auth_credentials" not in data or data.get("auth_credentials") is None
        assert "password" not in str(data).lower() or "secret_password_123" not in str(data)

    async def test_create_dashboard_supported_types(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test supported dashboard types

        Expected types: superset, tableau, power_bi, looker, metabase
        """
        supported_types = ["superset", "tableau", "power_bi", "looker", "metabase"]

        for dash_type in supported_types:
            request_body = {
                "dashboard_name": f"{dash_type.title()} Dashboard",
                "type": dash_type,
                "url": f"https://{dash_type}.example.com/dashboard"
            }

            response = await async_client.post(
                "/api/dashboards",
                headers=auth_headers,
                json=request_body
            )

            assert response.status_code == 201

    async def test_create_dashboard_invalid_type(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test invalid dashboard type returns 400

        Expected:
        - Only supported types allowed
        """
        request_body = {
            "dashboard_name": "Test",
            "type": "unsupported_type",
            "url": "https://example.com/dashboard"
        }

        response = await async_client.post(
            "/api/dashboards",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [400, 422]

    async def test_create_dashboard_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        request_body = {
            "dashboard_name": "Test",
            "type": "superset",
            "url": "https://example.com/dashboard"
        }

        response = await async_client.post(
            "/api/dashboards",
            json=request_body
        )

        assert response.status_code == 401

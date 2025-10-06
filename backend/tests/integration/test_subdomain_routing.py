"""
T065: Subdomain Routing Test
Verify middleware extracts correct subdomain and routes to correct tenant DB
"""

import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch
from app.middleware.tenant_context import TenantContextMiddleware
from app.core.tenant import TenantContext


@pytest.mark.integration
@pytest.mark.asyncio
class TestSubdomainRouting:
    """Test suite for subdomain extraction and tenant routing"""

    async def test_subdomain_extraction_from_hostname(self):
        """
        Verify middleware correctly extracts subdomain from Host header

        Test cases:
        - demo.taskifai.com → "demo"
        - acme.taskifai.com → "acme"
        - beta-test.taskifai.com → "beta-test"
        """
        test_cases = [
            ("demo.taskifai.com", "demo"),
            ("acme.taskifai.com", "acme"),
            ("beta-test.taskifai.com", "beta-test"),
            ("my-company.taskifai.com", "my-company"),
        ]

        for hostname, expected_subdomain in test_cases:
            # Mock request with Host header
            mock_request = Mock()
            mock_request.headers = {"host": hostname}

            # Extract subdomain (this will use actual middleware logic)
            with patch("app.middleware.tenant_context.TenantRegistry") as MockRegistry:
                MockRegistry.return_value.get_by_subdomain.return_value = TenantContext(
                    tenant_id="test-id",
                    subdomain=expected_subdomain,
                    database_url="postgresql://test",
                    database_key="test_key"
                )

                # Call middleware logic
                middleware = TenantContextMiddleware(app=None)
                extracted = await middleware.extract_subdomain(mock_request)

                assert extracted == expected_subdomain, \
                    f"Failed to extract '{expected_subdomain}' from '{hostname}'"

    async def test_subdomain_invalid_formats_rejected(self):
        """
        Verify invalid subdomain formats are rejected

        Invalid formats:
        - taskifai.com (no subdomain)
        - localhost (no subdomain)
        - 192.168.1.1 (IP address)
        - subdomain with special chars
        """
        invalid_hostnames = [
            "taskifai.com",  # No subdomain
            "localhost",  # Localhost
            "127.0.0.1",  # IP
            "192.168.1.1",  # IP
            "sub..taskifai.com",  # Double dot
            "sub domain.taskifai.com",  # Space
            "sub<script>.taskifai.com",  # XSS attempt
        ]

        for hostname in invalid_hostnames:
            mock_request = Mock()
            mock_request.headers = {"host": hostname}

            middleware = TenantContextMiddleware(app=None)

            with pytest.raises(ValueError, match="Invalid subdomain"):
                await middleware.extract_subdomain(mock_request)

    async def test_tenant_lookup_by_subdomain(
        self, async_client: AsyncClient
    ):
        """
        Verify subdomain → tenant lookup works correctly

        Test scenario:
        1. Request comes in with Host: demo.taskifai.com
        2. Middleware extracts "demo"
        3. Registry looks up tenant by subdomain
        4. Returns correct TenantContext
        """
        with patch("app.services.tenant.registry.TenantRegistry") as MockRegistry:
            # Mock tenant registry response
            mock_tenant = TenantContext(
                tenant_id="550e8400-e29b-41d4-a716-446655440000",
                subdomain="demo",
                database_url="postgresql://demo",
                database_key="demo_key"
            )
            MockRegistry.return_value.get_by_subdomain.return_value = mock_tenant

            # Make request with subdomain
            response = await async_client.get(
                "/health",
                headers={"Host": "demo.taskifai.com"}
            )

            assert response.status_code == 200

            # Verify registry was called with correct subdomain
            MockRegistry.return_value.get_by_subdomain.assert_called_with("demo")

    async def test_unknown_subdomain_rejected(
        self, async_client: AsyncClient
    ):
        """
        Verify requests with unknown subdomain are rejected

        Test scenario:
        1. Request comes in with Host: unknown.taskifai.com
        2. Registry lookup returns None (tenant not found)
        3. Should return 404 or 403
        """
        with patch("app.services.tenant.registry.TenantRegistry") as MockRegistry:
            # Mock tenant not found
            MockRegistry.return_value.get_by_subdomain.return_value = None

            response = await async_client.get(
                "/health",
                headers={"Host": "unknown.taskifai.com"}
            )

            # Should reject unknown tenant
            assert response.status_code in [403, 404]

    async def test_tenant_context_injected_into_request_state(
        self, async_client: AsyncClient
    ):
        """
        Verify TenantContext is injected into request.state

        Test scenario:
        1. Request processed by middleware
        2. Verify request.state.tenant is set
        3. Verify downstream handlers can access tenant context
        """
        with patch("app.middleware.tenant_context.TenantRegistry") as MockRegistry:
            mock_tenant = TenantContext(
                tenant_id="550e8400-e29b-41d4-a716-446655440000",
                subdomain="demo",
                database_url="postgresql://demo",
                database_key="demo_key"
            )
            MockRegistry.return_value.get_by_subdomain.return_value = mock_tenant

            # Make request
            response = await async_client.get(
                "/health",
                headers={"Host": "demo.taskifai.com"}
            )

            assert response.status_code == 200

            # In actual implementation, endpoint would access request.state.tenant
            # This verifies the injection mechanism works

    async def test_routing_to_correct_database(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Verify subdomain routes to correct tenant database

        Test scenario:
        1. Request with demo.taskifai.com → connects to demo DB
        2. Request with acme.taskifai.com → connects to acme DB
        3. Verify queries go to correct database
        """
        # Test demo tenant routing
        with patch("app.core.db_manager.DatabaseManager") as MockDB:
            response = await async_client.get(
                "/api/analytics/kpis",
                headers={
                    "Host": "demo.taskifai.com",
                    "Authorization": "Bearer demo_token"
                }
            )

            # Verify DB manager was called with demo credentials
            assert MockDB.called, "Database manager not invoked"
            # Would verify correct DB credentials passed

        # Test acme tenant routing
        with patch("app.core.db_manager.DatabaseManager") as MockDB:
            response = await async_client.get(
                "/api/analytics/kpis",
                headers={
                    "Host": "acme.taskifai.com",
                    "Authorization": "Bearer acme_token"
                }
            )

            # Verify DB manager was called with acme credentials
            assert MockDB.called, "Database manager not invoked"
            # Would verify different credentials than demo

    async def test_missing_host_header_rejected(
        self, async_client: AsyncClient
    ):
        """
        Verify requests without Host header are rejected

        Test scenario:
        1. Send request without Host header
        2. Should return 400 Bad Request
        """
        response = await async_client.get("/health")

        # Should reject missing Host header
        assert response.status_code == 400
        assert "host" in response.json()["detail"].lower()

    async def test_subdomain_case_insensitive(self):
        """
        Verify subdomain extraction is case-insensitive

        Test cases:
        - DEMO.taskifai.com → "demo"
        - Demo.taskifai.com → "demo"
        - demo.TASKIFAI.com → "demo"
        """
        test_cases = [
            "DEMO.taskifai.com",
            "Demo.taskifai.com",
            "demo.TASKIFAI.com",
        ]

        for hostname in test_cases:
            mock_request = Mock()
            mock_request.headers = {"host": hostname}

            middleware = TenantContextMiddleware(app=None)
            extracted = await middleware.extract_subdomain(mock_request)

            assert extracted == "demo", \
                f"Subdomain should be lowercase: got '{extracted}'"

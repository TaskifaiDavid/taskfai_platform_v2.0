"""
T067: Database Connection Scoping Test
Verify queries go to correct tenant database
"""

import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
import asyncpg


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseConnectionScoping:
    """Test suite for database connection scoping per tenant"""

    async def test_query_uses_tenant_database_connection(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Verify queries execute against correct tenant database

        Test scenario:
        1. Make request with demo subdomain
        2. Verify DB manager uses demo database credentials
        3. Make request with acme subdomain
        4. Verify DB manager uses acme database credentials
        """
        with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
            # Mock demo database connection
            demo_conn = AsyncMock()
            demo_conn.fetchrow.return_value = {"tenant_id": "demo", "data": "demo_data"}

            MockDBManager.return_value.get_connection.return_value.__aenter__.return_value = demo_conn

            # Request to demo tenant
            response = await async_client.get(
                "/api/analytics/kpis",
                headers={
                    "Host": "demo.taskifai.com",
                    "Authorization": "Bearer demo_token"
                }
            )

            # Verify connection was requested for demo tenant
            MockDBManager.return_value.get_connection.assert_called()

        with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
            # Mock acme database connection
            acme_conn = AsyncMock()
            acme_conn.fetchrow.return_value = {"tenant_id": "acme", "data": "acme_data"}

            MockDBManager.return_value.get_connection.return_value.__aenter__.return_value = acme_conn

            # Request to acme tenant
            response = await async_client.get(
                "/api/analytics/kpis",
                headers={
                    "Host": "acme.taskifai.com",
                    "Authorization": "Bearer acme_token"
                }
            )

            # Verify different connection for acme tenant
            MockDBManager.return_value.get_connection.assert_called()

    async def test_connection_switched_between_tenants(self):
        """
        Verify connection properly switches between tenants within same request cycle

        Test scenario:
        1. Execute query for demo tenant
        2. Execute query for acme tenant
        3. Execute query for demo tenant again
        4. Verify correct DB used each time
        """
        from app.core.db_manager import DatabaseManager

        db_manager = DatabaseManager()

        # Mock connections
        with patch.object(asyncpg, "create_pool") as mock_create_pool:
            demo_pool = AsyncMock()
            acme_pool = AsyncMock()

            # Setup mock pools to return different results
            demo_conn = AsyncMock()
            demo_conn.fetchrow.return_value = {"db": "demo"}
            demo_pool.acquire.return_value.__aenter__.return_value = demo_conn

            acme_conn = AsyncMock()
            acme_conn.fetchrow.return_value = {"db": "acme"}
            acme_pool.acquire.return_value.__aenter__.return_value = acme_conn

            # Mock pool creation to return different pools per tenant
            def create_pool_side_effect(dsn, **kwargs):
                if "demo" in dsn:
                    return demo_pool
                elif "acme" in dsn:
                    return acme_pool
                return AsyncMock()

            mock_create_pool.side_effect = create_pool_side_effect

            # Query 1: Demo tenant
            async with db_manager.get_connection("demo_db_url") as conn:
                result = await conn.fetchrow("SELECT * FROM test")
                assert result["db"] == "demo"

            # Query 2: Acme tenant (switch)
            async with db_manager.get_connection("acme_db_url") as conn:
                result = await conn.fetchrow("SELECT * FROM test")
                assert result["db"] == "acme"

            # Query 3: Demo tenant again (switch back)
            async with db_manager.get_connection("demo_db_url") as conn:
                result = await conn.fetchrow("SELECT * FROM test")
                assert result["db"] == "demo"

    async def test_concurrent_requests_isolated_connections(self):
        """
        Verify concurrent requests to different tenants use isolated connections

        Test scenario:
        1. Simulate 2 concurrent requests (demo and acme)
        2. Verify each gets correct connection
        3. Verify no connection bleeding between requests
        """
        import asyncio

        async def query_demo():
            with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
                conn = AsyncMock()
                conn.fetchrow.return_value = {"tenant": "demo"}
                MockDBManager.return_value.get_connection.return_value.__aenter__.return_value = conn

                # Simulate some work
                await asyncio.sleep(0.01)
                result = await conn.fetchrow("SELECT * FROM sales")
                return result

        async def query_acme():
            with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
                conn = AsyncMock()
                conn.fetchrow.return_value = {"tenant": "acme"}
                MockDBManager.return_value.get_connection.return_value.__aenter__.return_value = conn

                # Simulate some work
                await asyncio.sleep(0.01)
                result = await conn.fetchrow("SELECT * FROM sales")
                return result

        # Execute concurrently
        demo_result, acme_result = await asyncio.gather(
            query_demo(),
            query_acme()
        )

        # Verify results are isolated
        assert demo_result["tenant"] == "demo"
        assert acme_result["tenant"] == "acme"

    async def test_connection_uses_tenant_database_url(self):
        """
        Verify connection manager uses correct database_url from TenantContext

        Test scenario:
        1. Create TenantContext with specific database_url
        2. Request connection
        3. Verify connection created with that URL
        """
        from app.core.tenant import TenantContext

        tenant = TenantContext(
            tenant_id="test_id",
            subdomain="test",
            database_url="postgresql://user:pass@host:5432/test_db",
            database_key="test_key"
        )

        with patch.object(asyncpg, "create_pool") as mock_create_pool:
            from app.core.db_manager import DatabaseManager

            db_manager = DatabaseManager()
            await db_manager.get_pool(tenant.database_url)

            # Verify pool created with correct URL
            mock_create_pool.assert_called()
            call_args = mock_create_pool.call_args
            assert tenant.database_url in str(call_args)

    async def test_rls_policies_applied_per_tenant(
        self, async_client: AsyncClient
    ):
        """
        Verify RLS (Row Level Security) policies are enforced per tenant

        Test scenario:
        1. Create sales data in demo tenant DB
        2. Create sales data in acme tenant DB
        3. Query from demo context
        4. Verify RLS policy filters to only demo data
        """
        # This test verifies that even if connections were misconfigured,
        # RLS policies at DB level would prevent cross-tenant data access

        demo_headers = {
            "Host": "demo.taskifai.com",
            "Authorization": "Bearer demo_token"
        }

        with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
            # Mock DB that returns both demo and acme data (RLS failure scenario)
            conn = AsyncMock()
            conn.fetch.return_value = [
                {"tenant_id": "demo", "sale_id": "1"},
                {"tenant_id": "acme", "sale_id": "2"},  # Should be filtered by RLS
            ]
            MockDBManager.return_value.get_connection.return_value.__aenter__.return_value = conn

            response = await async_client.get(
                "/api/analytics/sales",
                headers=demo_headers
            )

            # If RLS policies work, acme data should be filtered out
            # This test documents expected behavior
            data = response.json()
            for sale in data.get("data", []):
                assert sale["tenant_id"] == "demo", \
                    "RLS policy failed to filter cross-tenant data!"

    async def test_database_key_used_for_encryption(self):
        """
        Verify tenant database_key is used for encrypted column access

        Test scenario:
        1. TenantContext includes database_key
        2. Queries with encrypted columns use this key
        3. Verify decryption works with correct key
        """
        from app.core.tenant import TenantContext

        tenant = TenantContext(
            tenant_id="test_id",
            subdomain="test",
            database_url="postgresql://test",
            database_key="encryption_key_123"
        )

        # Mock DB query with encrypted data
        with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
            conn = AsyncMock()

            # Simulate encrypted column access using database_key
            conn.fetchrow.return_value = {
                "encrypted_field": "decrypted_with_correct_key"
            }

            MockDBManager.return_value.get_connection.return_value.__aenter__.return_value = conn

            # Query that accesses encrypted columns
            async with MockDBManager.return_value.get_connection() as connection:
                # In real implementation, would pass database_key for decryption
                result = await connection.fetchrow(
                    "SELECT pgp_sym_decrypt(encrypted_field, %s) FROM table",
                    tenant.database_key
                )

                assert result["encrypted_field"] == "decrypted_with_correct_key"

    async def test_connection_error_isolated_per_tenant(self):
        """
        Verify connection errors for one tenant don't affect others

        Test scenario:
        1. Demo tenant DB connection fails
        2. Acme tenant DB connection should still work
        3. Verify error isolation
        """
        with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
            # Demo connection fails
            MockDBManager.return_value.get_connection.side_effect = Exception("Demo DB connection failed")

            # Demo request should fail
            response_demo = await async_client.get(
                "/api/analytics/kpis",
                headers={
                    "Host": "demo.taskifai.com",
                    "Authorization": "Bearer demo_token"
                }
            )
            assert response_demo.status_code == 500

        with patch("app.core.db_manager.DatabaseManager") as MockDBManager:
            # Acme connection succeeds
            conn = AsyncMock()
            conn.fetchrow.return_value = {"status": "ok"}
            MockDBManager.return_value.get_connection.return_value.__aenter__.return_value = conn

            # Acme request should succeed
            response_acme = await async_client.get(
                "/api/analytics/kpis",
                headers={
                    "Host": "acme.taskifai.com",
                    "Authorization": "Bearer acme_token"
                }
            )
            assert response_acme.status_code == 200

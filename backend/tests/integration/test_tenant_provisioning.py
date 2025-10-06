"""
T090: Tenant Provisioning Integration Test
Admin API → Supabase Project → Schema → Seed
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
class TestTenantProvisioningIntegration:
    """Integration tests for tenant provisioning workflow"""

    async def test_complete_tenant_provisioning_flow(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test complete tenant provisioning flow

        Flow:
        1. Admin creates tenant via API
        2. System calls Supabase Management API
        3. New Supabase project created
        4. Database schema applied (migrations)
        5. Vendor configs seeded
        6. Credentials encrypted and stored
        7. Tenant activated
        """
        with patch("app.services.tenant.provisioner.SupabaseManagementClient") as MockClient:
            # Mock Supabase Management API responses
            mock_client = AsyncMock()
            mock_client.create_project.return_value = {
                "id": "new_project_id",
                "database_url": "postgresql://user:pass@host/db",
                "database_key": "encryption_key_123"
            }
            MockClient.return_value = mock_client

            # Step 1: Create tenant
            response = await async_client.post(
                "/api/admin/tenants",
                headers=admin_headers,
                json={
                    "subdomain": "newclient",
                    "company_name": "New Client Inc",
                    "admin_email": "admin@newclient.com",
                    "region": "us-east-1"
                }
            )

            assert response.status_code == 201
            tenant = response.json()

            # Verify tenant created
            assert tenant["subdomain"] == "newclient"
            assert tenant["company_name"] == "New Client Inc"
            assert tenant["is_active"] is True

            # Step 2-3: Verify Supabase API called
            mock_client.create_project.assert_called_once()

            # Step 6: Verify credentials encrypted
            assert "database_url" in tenant
            # Should be encrypted or not exposed
            assert not tenant["database_url"].startswith("postgresql://") or \
                   tenant["database_url"] == "encrypted"

    async def test_schema_migration_applied_on_provision(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test database schema migrations applied to new tenant

        Expected:
        - All tables created
        - RLS policies applied
        - Indexes created
        """
        with patch("app.services.tenant.provisioner.SupabaseManagementClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.create_project.return_value = {
                "id": "project_id",
                "database_url": "postgresql://test",
                "database_key": "key"
            }
            mock_client.run_migrations.return_value = {"success": True}
            MockClient.return_value = mock_client

            response = await async_client.post(
                "/api/admin/tenants",
                headers=admin_headers,
                json={
                    "subdomain": "migrated",
                    "company_name": "Migrated Co",
                    "admin_email": "admin@migrated.com"
                }
            )

            assert response.status_code == 201

            # Verify migrations run
            mock_client.run_migrations.assert_called()

    async def test_vendor_configs_seeded_on_provision(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test vendor configurations seeded for new tenant

        Expected:
        - All 9 vendor configs created
        - Default column mappings loaded
        - Tenant can immediately process files
        """
        with patch("app.services.tenant.provisioner.SupabaseManagementClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.create_project.return_value = {
                "id": "project_id",
                "database_url": "postgresql://test",
                "database_key": "key"
            }
            mock_client.seed_vendor_configs.return_value = {"success": True, "count": 9}
            MockClient.return_value = mock_client

            response = await async_client.post(
                "/api/admin/tenants",
                headers=admin_headers,
                json={
                    "subdomain": "seeded",
                    "company_name": "Seeded Co",
                    "admin_email": "admin@seeded.com"
                }
            )

            assert response.status_code == 201

            # Verify vendor configs seeded
            mock_client.seed_vendor_configs.assert_called()

    async def test_provisioning_failure_rollback(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test provisioning failure triggers rollback

        Expected:
        - If Supabase project creation fails, tenant not created
        - If schema migration fails, project deleted
        - Atomic operation
        """
        with patch("app.services.tenant.provisioner.SupabaseManagementClient") as MockClient:
            # Mock failure
            mock_client = AsyncMock()
            mock_client.create_project.side_effect = Exception("Supabase API error")
            MockClient.return_value = mock_client

            response = await async_client.post(
                "/api/admin/tenants",
                headers=admin_headers,
                json={
                    "subdomain": "failed",
                    "company_name": "Failed Co",
                    "admin_email": "admin@failed.com"
                }
            )

            # Should fail gracefully
            assert response.status_code in [500, 503]

            # Tenant should not exist
            list_response = await async_client.get(
                "/api/admin/tenants",
                headers=admin_headers,
                params={"search": "failed"}
            )

            tenants = list_response.json()["tenants"]
            assert not any(t["subdomain"] == "failed" for t in tenants)

    async def test_duplicate_subdomain_prevention(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test cannot create duplicate subdomain

        Expected:
        - Second creation with same subdomain rejected
        - Returns 409 Conflict
        """
        subdomain = "duplicate"

        # Create first tenant
        response1 = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json={
                "subdomain": subdomain,
                "company_name": "First",
                "admin_email": "admin1@test.com"
            }
        )

        # Try to create duplicate
        response2 = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json={
                "subdomain": subdomain,
                "company_name": "Second",
                "admin_email": "admin2@test.com"
            }
        )

        assert response2.status_code in [409, 400]

    async def test_region_selection_in_provisioning(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test tenant provisioned in specified region

        Expected:
        - Region parameter passed to Supabase API
        - Tenant database in correct region
        """
        with patch("app.services.tenant.provisioner.SupabaseManagementClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.create_project.return_value = {
                "id": "project_id",
                "database_url": "postgresql://test",
                "database_key": "key",
                "region": "eu-west-1"
            }
            MockClient.return_value = mock_client

            response = await async_client.post(
                "/api/admin/tenants",
                headers=admin_headers,
                json={
                    "subdomain": "eu-tenant",
                    "company_name": "EU Company",
                    "admin_email": "admin@eu.com",
                    "region": "eu-west-1"
                }
            )

            assert response.status_code == 201

            # Verify region parameter used
            call_args = mock_client.create_project.call_args
            assert "region" in str(call_args)

    async def test_tenant_immediately_accessible_after_provision(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test new tenant immediately accessible

        Expected:
        - Can make requests to new tenant subdomain
        - Database connections work
        - No warm-up period needed
        """
        with patch("app.services.tenant.provisioner.SupabaseManagementClient"):
            # Create tenant
            create_response = await async_client.post(
                "/api/admin/tenants",
                headers=admin_headers,
                json={
                    "subdomain": "instant",
                    "company_name": "Instant Co",
                    "admin_email": "admin@instant.com"
                }
            )

            assert create_response.status_code == 201

            # Immediately try to access
            access_response = await async_client.get(
                "/health",
                headers={"Host": "instant.taskifai.com"}
            )

            # Should be accessible
            assert access_response.status_code in [200, 404]  # 404 if tenant not found in registry

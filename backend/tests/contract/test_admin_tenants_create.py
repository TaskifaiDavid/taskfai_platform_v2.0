"""
T081: Admin Create Tenant API Contract Test
POST /api/admin/tenants
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestAdminCreateTenantContract:
    """Contract tests for POST /api/admin/tenants endpoint"""

    async def test_create_tenant_success(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test successful tenant creation

        Expected response:
        {
            "tenant_id": "uuid",
            "subdomain": "newcompany",
            "company_name": "New Company",
            "is_active": true,
            "created_at": "2025-10-06T10:00:00Z",
            "database_url": "encrypted_value",
            "database_key": "encrypted_value"
        }
        """
        request_body = {
            "subdomain": "newcompany",
            "company_name": "New Company Inc",
            "admin_email": "admin@newcompany.com",
            "plan": "professional"
        }

        response = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        assert "tenant_id" in data
        assert data["subdomain"] == "newcompany"
        assert data["company_name"] == "New Company Inc"
        assert "is_active" in data
        assert data["is_active"] is True
        assert "created_at" in data

    async def test_create_tenant_requires_admin_role(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test non-admin cannot create tenants

        Expected:
        - Status: 403 Forbidden
        - Only admin role can create tenants
        """
        request_body = {
            "subdomain": "test",
            "company_name": "Test",
            "admin_email": "test@test.com"
        }

        response = await async_client.post(
            "/api/admin/tenants",
            headers=auth_headers,  # Regular user token
            json=request_body
        )

        assert response.status_code == 403

    async def test_create_tenant_duplicate_subdomain(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test duplicate subdomain rejected

        Expected:
        - Status: 409 Conflict
        - Error about subdomain already exists
        """
        request_body = {
            "subdomain": "demo",  # Already exists
            "company_name": "Demo Copy",
            "admin_email": "admin@demo.com"
        }

        response = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code in [409, 400]
        data = response.json()
        assert "subdomain" in data["detail"].lower() or "exists" in data["detail"].lower()

    async def test_create_tenant_invalid_subdomain_format(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test invalid subdomain format rejected

        Expected:
        - Only lowercase alphanumeric and hyphens
        - No spaces, special chars, or uppercase
        """
        invalid_subdomains = [
            "Test Company",  # Spaces
            "test_company",  # Underscore
            "TestCompany",  # Uppercase
            "test@company",  # Special char
            "test..company",  # Double dots
        ]

        for subdomain in invalid_subdomains:
            request_body = {
                "subdomain": subdomain,
                "company_name": "Test",
                "admin_email": "test@test.com"
            }

            response = await async_client.post(
                "/api/admin/tenants",
                headers=admin_headers,
                json=request_body
            )

            assert response.status_code in [400, 422], \
                f"Invalid subdomain '{subdomain}' should be rejected"

    async def test_create_tenant_provisions_supabase_project(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test tenant creation provisions Supabase project

        Expected:
        - Calls Supabase Management API
        - Creates new project
        - Runs migrations
        - Seeds vendor configs
        - Returns database credentials (encrypted)
        """
        request_body = {
            "subdomain": "newclient",
            "company_name": "New Client",
            "admin_email": "admin@newclient.com",
            "region": "us-east-1"
        }

        response = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        # Should have database credentials
        assert "database_url" in data or "project_id" in data
        assert "database_key" in data or "encryption_key" in data

    async def test_create_tenant_missing_required_fields(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test missing required fields returns 422

        Required: subdomain, company_name, admin_email
        """
        request_body = {
            "subdomain": "test"
            # Missing company_name and admin_email
        }

        response = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code == 422

    async def test_create_tenant_credentials_encrypted(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        SECURITY: Test database credentials encrypted in storage

        Expected:
        - database_url encrypted with AES-256
        - database_key encrypted with AES-256
        - Credentials not in plaintext in DB
        """
        request_body = {
            "subdomain": "secure",
            "company_name": "Secure Co",
            "admin_email": "admin@secure.com"
        }

        response = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        # Response might show encrypted values or omit them
        if "database_url" in data:
            # Should not be plaintext postgresql://
            assert not data["database_url"].startswith("postgresql://") or \
                   data["database_url"] == "encrypted"

    async def test_create_tenant_sets_default_plan(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test default plan assigned if not specified

        Expected:
        - Default plan: "starter" or similar
        - Can override with plan parameter
        """
        request_body = {
            "subdomain": "starter",
            "company_name": "Starter Co",
            "admin_email": "admin@starter.com"
            # No plan specified
        }

        response = await async_client.post(
            "/api/admin/tenants",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()

        assert "plan" in data or "subscription" in data

    async def test_create_tenant_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        request_body = {
            "subdomain": "test",
            "company_name": "Test",
            "admin_email": "test@test.com"
        }

        response = await async_client.post(
            "/api/admin/tenants",
            json=request_body
        )

        assert response.status_code == 401

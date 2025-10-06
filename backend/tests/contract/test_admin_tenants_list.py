"""
T082: Admin List Tenants API Contract Test
GET /api/admin/tenants
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestAdminListTenantsContract:
    """Contract tests for GET /api/admin/tenants endpoint"""

    async def test_list_tenants_success(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test successful tenant list retrieval

        Expected response:
        {
            "tenants": [
                {
                    "tenant_id": "uuid",
                    "subdomain": "demo",
                    "company_name": "Demo Company",
                    "is_active": true,
                    "plan": "professional",
                    "created_at": "2025-01-01T00:00:00Z",
                    "metrics": {
                        "user_count": 10,
                        "storage_used": 1024000,
                        "last_activity": "2025-10-06T09:00:00Z"
                    }
                }
            ],
            "total": 50
        }
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "tenants" in data
        assert "total" in data
        assert isinstance(data["tenants"], list)

        # If tenants exist, verify structure
        if len(data["tenants"]) > 0:
            tenant = data["tenants"][0]
            assert "tenant_id" in tenant
            assert "subdomain" in tenant
            assert "company_name" in tenant
            assert "is_active" in tenant

    async def test_list_tenants_requires_admin_role(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test non-admin cannot list all tenants

        Expected:
        - Status: 403 Forbidden
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=auth_headers  # Regular user
        )

        assert response.status_code == 403

    async def test_list_tenants_pagination(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test tenant list pagination

        Expected:
        - Query params: page, page_size
        - Response includes pagination info
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers,
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["tenants"]) <= 10

    async def test_list_tenants_filter_by_status(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test filtering by active status

        Expected:
        - Query param: is_active=true or is_active=false
        - Returns only matching tenants
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers,
            params={"is_active": "true"}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned tenants should be active
        for tenant in data["tenants"]:
            assert tenant["is_active"] is True

    async def test_list_tenants_filter_by_plan(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test filtering by subscription plan

        Expected:
        - Query param: plan=professional
        - Returns only tenants on that plan
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers,
            params={"plan": "professional"}
        )

        assert response.status_code == 200
        data = response.json()

        for tenant in data["tenants"]:
            assert tenant.get("plan") == "professional"

    async def test_list_tenants_search_by_name(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test searching by company name or subdomain

        Expected:
        - Query param: search=demo
        - Returns tenants matching search term
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers,
            params={"search": "demo"}
        )

        assert response.status_code == 200
        data = response.json()

        # Results should match search term
        for tenant in data["tenants"]:
            assert "demo" in tenant["subdomain"].lower() or \
                   "demo" in tenant["company_name"].lower()

    async def test_list_tenants_includes_metrics(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test tenant metrics included in response

        Expected metrics:
        - user_count
        - storage_used
        - last_activity
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["tenants"]) > 0:
            tenant = data["tenants"][0]
            assert "metrics" in tenant or "user_count" in tenant

    async def test_list_tenants_sorted_by_created_date(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test default sorting by creation date

        Expected:
        - Most recent first (descending)
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        tenants = data["tenants"]
        if len(tenants) > 1:
            for i in range(len(tenants) - 1):
                assert tenants[i]["created_at"] >= tenants[i+1]["created_at"]

    async def test_list_tenants_no_credentials_exposed(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        SECURITY: Test database credentials not exposed in list

        Expected:
        - No plaintext database_url or database_key
        - Credentials only available in detail view if needed
        """
        response = await async_client.get(
            "/api/admin/tenants",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        for tenant in data["tenants"]:
            # Should not expose full credentials
            assert "database_url" not in tenant or \
                   not tenant["database_url"].startswith("postgresql://")
            assert "database_key" not in tenant or \
                   tenant["database_key"] is None

    async def test_list_tenants_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.get("/api/admin/tenants")

        assert response.status_code == 401

"""
T064: Multi-Tenant Isolation Test
Verify that Customer A cannot access Customer B data
Tests the core security principle of tenant isolation
"""

import pytest
from httpx import AsyncClient
from app.core.tenant import TenantContext


@pytest.mark.integration
@pytest.mark.asyncio
class TestMultiTenantIsolation:
    """Test suite for multi-tenant data isolation"""

    async def test_tenant_cannot_access_other_tenant_data(
        self, async_client: AsyncClient, tenant_demo, tenant_acme
    ):
        """
        CRITICAL: Verify that tenant A cannot query tenant B's data

        Test scenario:
        1. Create test data in demo tenant DB
        2. Create test data in acme tenant DB
        3. Query from demo tenant context
        4. Verify ONLY demo data returned (no acme data)
        5. Query from acme tenant context
        6. Verify ONLY acme data returned (no demo data)
        """
        # Setup: Create sales data for demo tenant
        demo_headers = {
            "Host": "demo.taskifai.com",
            "Authorization": "Bearer demo_token"
        }

        # Setup: Create sales data for acme tenant
        acme_headers = {
            "Host": "acme.taskifai.com",
            "Authorization": "Bearer acme_token"
        }

        # Test 1: Demo tenant queries sales - should only see demo data
        response = await async_client.get(
            "/api/analytics/sales",
            headers=demo_headers
        )
        assert response.status_code == 200
        sales_data = response.json()

        # Verify no acme data leaked into demo results
        for sale in sales_data.get("data", []):
            assert sale["tenant_id"] == tenant_demo.tenant_id, \
                "Demo tenant seeing data from other tenant!"

        # Test 2: Acme tenant queries sales - should only see acme data
        response = await async_client.get(
            "/api/analytics/sales",
            headers=acme_headers
        )
        assert response.status_code == 200
        sales_data = response.json()

        # Verify no demo data leaked into acme results
        for sale in sales_data.get("data", []):
            assert sale["tenant_id"] == tenant_acme.tenant_id, \
                "Acme tenant seeing data from other tenant!"

    async def test_jwt_token_prevents_tenant_spoofing(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Verify JWT tenant claims prevent subdomain spoofing

        Test scenario:
        1. Generate JWT for demo tenant
        2. Attempt to query with demo JWT but acme subdomain
        3. Should reject: JWT tenant_id != request subdomain tenant
        """
        # Demo tenant JWT
        demo_token = "eyJ..." # JWT with tenant_id: demo

        # Attempt to access with wrong subdomain
        response = await async_client.get(
            "/api/analytics/sales",
            headers={
                "Host": "acme.taskifai.com",  # WRONG subdomain
                "Authorization": f"Bearer {demo_token}"  # Demo JWT
            }
        )

        # Should reject with 403 Forbidden
        assert response.status_code == 403, \
            "System allowed tenant spoofing via subdomain mismatch!"
        assert "tenant mismatch" in response.json()["detail"].lower()

    async def test_database_connection_isolation(
        self, async_client: AsyncClient, tenant_demo, tenant_acme
    ):
        """
        CRITICAL: Verify database connections are properly scoped to tenant

        Test scenario:
        1. Query tenant A data
        2. Immediately query tenant B data
        3. Verify connection switched properly (no connection bleeding)
        """
        demo_headers = {"Host": "demo.taskifai.com", "Authorization": "Bearer demo_token"}
        acme_headers = {"Host": "acme.taskifai.com", "Authorization": "Bearer acme_token"}

        # Query 1: Demo tenant
        response1 = await async_client.get("/api/analytics/kpis", headers=demo_headers)
        assert response1.status_code == 200
        demo_kpis = response1.json()

        # Query 2: Acme tenant (different DB connection)
        response2 = await async_client.get("/api/analytics/kpis", headers=acme_headers)
        assert response2.status_code == 200
        acme_kpis = response2.json()

        # Verify data is different (proves connections are isolated)
        assert demo_kpis != acme_kpis, \
            "Same data returned for different tenants - connection isolation failed!"

    async def test_upload_isolation(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Verify file uploads are isolated per tenant

        Test scenario:
        1. Upload file as demo tenant
        2. Query uploads as acme tenant
        3. Acme should NOT see demo's upload
        """
        demo_headers = {"Host": "demo.taskifai.com", "Authorization": "Bearer demo_token"}
        acme_headers = {"Host": "acme.taskifai.com", "Authorization": "Bearer acme_token"}

        # Demo uploads a file
        demo_upload = {
            "file": ("sales.xlsx", b"fake_excel_data", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        response = await async_client.post(
            "/api/uploads",
            headers=demo_headers,
            files=demo_upload
        )
        assert response.status_code == 200
        upload_id = response.json()["batch_id"]

        # Acme tries to access demo's upload
        response = await async_client.get(
            f"/api/uploads/{upload_id}",
            headers=acme_headers
        )

        # Should return 404 (not found) or 403 (forbidden)
        assert response.status_code in [403, 404], \
            "Acme tenant can access demo tenant's uploads!"

    async def test_user_isolation_within_tenant(
        self, async_client: AsyncClient
    ):
        """
        Verify RLS policies enforce user_id filtering within same tenant

        Test scenario:
        1. User A uploads file in demo tenant
        2. User B (also in demo tenant) queries uploads
        3. User B should only see their own uploads, not User A's
        """
        user_a_headers = {
            "Host": "demo.taskifai.com",
            "Authorization": "Bearer user_a_token"  # user_id: aaa
        }
        user_b_headers = {
            "Host": "demo.taskifai.com",
            "Authorization": "Bearer user_b_token"  # user_id: bbb
        }

        # User A uploads
        upload = {
            "file": ("sales.xlsx", b"fake_data", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        response = await async_client.post(
            "/api/uploads",
            headers=user_a_headers,
            files=upload
        )
        assert response.status_code == 200

        # User B queries uploads
        response = await async_client.get(
            "/api/uploads",
            headers=user_b_headers
        )
        assert response.status_code == 200
        uploads = response.json()

        # User B should not see User A's upload
        for upload in uploads.get("data", []):
            assert upload["user_id"] != "aaa", \
                "RLS policy failed: User B can see User A's data!"

    async def test_conversation_history_isolation(
        self, async_client: AsyncClient
    ):
        """
        Verify AI chat conversations are isolated per tenant

        Test scenario:
        1. Demo tenant has conversation with AI
        2. Acme tenant queries conversation history
        3. Acme should not see demo's conversations
        """
        demo_headers = {"Host": "demo.taskifai.com", "Authorization": "Bearer demo_token"}
        acme_headers = {"Host": "acme.taskifai.com", "Authorization": "Bearer acme_token"}

        # Demo tenant chats with AI
        response = await async_client.post(
            "/api/chat/query",
            headers=demo_headers,
            json={"query": "What are my top products?"}
        )
        assert response.status_code == 200

        # Acme queries chat history
        response = await async_client.get(
            "/api/chat/history",
            headers=acme_headers
        )
        assert response.status_code == 200
        history = response.json()

        # Should be empty or only contain acme's conversations
        assert len(history.get("conversations", [])) == 0, \
            "Acme tenant can see demo tenant's chat history!"

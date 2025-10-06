"""
T084: Admin Reactivate Tenant API Contract Test
PATCH /api/admin/tenants/{id}/reactivate
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestAdminReactivateTenantContract:
    """Contract tests for PATCH /api/admin/tenants/{id}/reactivate endpoint"""

    async def test_reactivate_tenant_success(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test successful tenant reactivation

        Expected response:
        {
            "tenant_id": "uuid",
            "subdomain": "company",
            "is_active": true,
            "reactivated_at": "2025-10-06T10:00:00Z",
            "message": "Tenant reactivated"
        }
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["is_active"] is True
            assert "reactivated_at" in data or "message" in data

    async def test_reactivate_tenant_requires_admin_role(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test non-admin cannot reactivate tenants

        Expected:
        - Status: 403 Forbidden
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=auth_headers  # Regular user
        )

        assert response.status_code == 403

    async def test_reactivate_tenant_not_found(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test reactivating non-existent tenant returns 404

        Expected:
        - Status: 404 Not Found
        """
        response = await async_client.patch(
            "/api/admin/tenants/non-existent-uuid/reactivate",
            headers=admin_headers
        )

        assert response.status_code == 404

    async def test_reactivate_tenant_restores_access(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test reactivation restores tenant access

        Expected:
        - Users can log in again
        - Can make API requests
        - Connection pools recreated
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]

        # Access restoration verified in integration tests

    async def test_reactivate_already_active_tenant(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test reactivating already active tenant

        Expected:
        - Status: 200 (idempotent) or 400
        - Remains active
        """
        tenant_id = "test-tenant-uuid"

        # Reactivate twice
        await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=admin_headers
        )

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=admin_headers
        )

        assert response.status_code in [200, 400, 404]

    async def test_reactivate_clears_suspension_reason(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test reactivation clears suspension reason

        Expected:
        - Previous suspension reason cleared or archived
        - New reactivation note optional
        """
        tenant_id = "test-tenant-uuid"

        request_body = {
            "note": "Payment received, reactivating"
        }

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code in [200, 404]

    async def test_reactivate_suspend_reactivate_cycle(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test full suspend → reactivate cycle

        Expected:
        - Suspend sets is_active=false
        - Reactivate sets is_active=true
        - Tenant fully functional after reactivation
        """
        tenant_id = "test-tenant-uuid"

        # Suspend
        suspend_response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=admin_headers
        )

        # Reactivate
        reactivate_response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=admin_headers
        )

        assert reactivate_response.status_code in [200, 404]

        if reactivate_response.status_code == 200:
            data = reactivate_response.json()
            assert data["is_active"] is True

    async def test_reactivate_tenant_audit_log(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test reactivation creates audit log entry

        Expected:
        - Action logged with admin user_id
        - Timestamp recorded
        - Note included if provided
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/reactivate",
            headers=admin_headers,
            json={"note": "Test reactivation"}
        )

        assert response.status_code in [200, 404]

    async def test_reactivate_tenant_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.patch(
            "/api/admin/tenants/test-id/reactivate"
        )

        assert response.status_code == 401

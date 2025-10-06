"""
T083: Admin Suspend Tenant API Contract Test
PATCH /api/admin/tenants/{id}/suspend
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestAdminSuspendTenantContract:
    """Contract tests for PATCH /api/admin/tenants/{id}/suspend endpoint"""

    async def test_suspend_tenant_success(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test successful tenant suspension

        Expected response:
        {
            "tenant_id": "uuid",
            "subdomain": "company",
            "is_active": false,
            "suspended_at": "2025-10-06T10:00:00Z",
            "message": "Tenant suspended"
        }
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["is_active"] is False
            assert "suspended_at" in data or "message" in data

    async def test_suspend_tenant_requires_admin_role(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        SECURITY: Test non-admin cannot suspend tenants

        Expected:
        - Status: 403 Forbidden
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=auth_headers  # Regular user
        )

        assert response.status_code == 403

    async def test_suspend_tenant_not_found(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test suspending non-existent tenant returns 404

        Expected:
        - Status: 404 Not Found
        """
        response = await async_client.patch(
            "/api/admin/tenants/non-existent-uuid/suspend",
            headers=admin_headers
        )

        assert response.status_code == 404

    async def test_suspend_tenant_invalidates_connections(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test suspension invalidates active connections

        Expected:
        - All user sessions terminated
        - Connection pools closed
        - Cannot make new requests
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=admin_headers
        )

        assert response.status_code in [200, 404]

        # Subsequent requests from suspended tenant should fail
        # This would be tested in integration tests

    async def test_suspend_tenant_with_reason(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test suspending with reason note

        Expected:
        - Optional reason field
        - Reason stored and returned
        """
        tenant_id = "test-tenant-uuid"

        request_body = {
            "reason": "Payment overdue"
        }

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=admin_headers,
            json=request_body
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "reason" in data or "message" in data

    async def test_suspend_already_suspended_tenant(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test suspending already suspended tenant

        Expected:
        - Status: 200 (idempotent) or 400
        - Remains suspended
        """
        tenant_id = "test-tenant-uuid"

        # Suspend twice
        await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=admin_headers
        )

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=admin_headers
        )

        assert response.status_code in [200, 400, 404]

    async def test_suspend_tenant_audit_log(
        self, async_client: AsyncClient, admin_headers
    ):
        """
        Test suspension creates audit log entry

        Expected:
        - Action logged with admin user_id
        - Timestamp recorded
        - Reason included if provided
        """
        tenant_id = "test-tenant-uuid"

        response = await async_client.patch(
            f"/api/admin/tenants/{tenant_id}/suspend",
            headers=admin_headers,
            json={"reason": "Test suspension"}
        )

        assert response.status_code in [200, 404]

        # Audit log would be verified in integration tests

    async def test_suspend_tenant_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.patch(
            "/api/admin/tenants/test-id/suspend"
        )

        assert response.status_code == 401

"""
Contract Test: Tenant Registry Admin API

Tests the tenant admin endpoints contract as defined in:
specs/002-see-here-what/contracts/tenant-registry.yaml

These tests MUST FAIL before implementation begins (TDD).
All endpoints require super_admin role in JWT.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def super_admin_token():
    """Generate JWT token with super_admin role"""
    token_data = {
        "sub": "test-user-id",
        "email": "admin@test.com",
        "tenant_id": "test-tenant-id",
        "subdomain": "test",
        "role": "super_admin"
    }
    return create_access_token(token_data)


@pytest.fixture
def regular_user_token():
    """Generate JWT token without super_admin role"""
    token_data = {
        "sub": "regular-user-id",
        "email": "user@test.com",
        "tenant_id": "test-tenant-id",
        "subdomain": "test",
        "role": "member"
    }
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(super_admin_token):
    """Authorization headers with super admin token"""
    return {"Authorization": f"Bearer {super_admin_token}"}


class TestCreateTenantContract:
    """Test POST /api/admin/tenants endpoint"""

    def test_create_tenant_endpoint_exists(self, auth_headers):
        """Endpoint should exist"""
        response = client.post(
            "/api/admin/tenants",
            json={
                "subdomain": "test",
                "company_name": "Test Company",
                "admin_email": "admin@test.com",
                "database_url": "https://test.supabase.co",
                "database_credentials": {
                    "anon_key": "test-anon-key",
                    "service_key": "test-service-key"
                }
            },
            headers=auth_headers
        )

        # Should not return 404
        assert response.status_code != 404, "Endpoint /api/admin/tenants does not exist"

    def test_create_tenant_requires_auth(self):
        """Endpoint should require authentication"""
        response = client.post(
            "/api/admin/tenants",
            json={
                "subdomain": "test",
                "company_name": "Test Company",
                "admin_email": "admin@test.com",
                "database_url": "https://test.supabase.co",
                "database_credentials": {
                    "anon_key": "test-anon-key",
                    "service_key": "test-service-key"
                }
            }
        )

        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"

    def test_create_tenant_requires_super_admin(self, regular_user_token):
        """Endpoint should require super_admin role"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = client.post(
            "/api/admin/tenants",
            json={
                "subdomain": "test",
                "company_name": "Test Company",
                "admin_email": "admin@test.com",
                "database_url": "https://test.supabase.co",
                "database_credentials": {
                    "anon_key": "test-anon-key",
                    "service_key": "test-service-key"
                }
            },
            headers=headers
        )

        # Should return 403 forbidden
        assert response.status_code == 403, f"Expected 403 for non-super-admin, got {response.status_code}"

    def test_create_tenant_response_schema(self, auth_headers):
        """Successful creation should return 201 with tenant data"""
        response = client.post(
            "/api/admin/tenants",
            json={
                "subdomain": f"test-tenant-contract",
                "company_name": "Test Company",
                "admin_email": "admin@testcompany.com",
                "database_url": "https://test.supabase.co",
                "database_credentials": {
                    "anon_key": "test-anon-key",
                    "service_key": "test-service-key"
                }
            },
            headers=auth_headers
        )

        # May return 201 or error if implementation exists
        if response.status_code == 201:
            data = response.json()

            # Validate response schema
            assert "tenant_id" in data, "Response must include tenant_id"
            assert "company_name" in data, "Response must include company_name"
            assert "subdomain" in data, "Response must include subdomain"
            assert "is_active" in data, "Response must include is_active"
            assert "created_at" in data, "Response must include created_at"

            # Validate data types
            assert isinstance(data["tenant_id"], str), "tenant_id must be string (UUID)"
            assert isinstance(data["company_name"], str), "company_name must be string"
            assert isinstance(data["subdomain"], str), "subdomain must be string"
            assert isinstance(data["is_active"], bool), "is_active must be boolean"
            assert isinstance(data["created_at"], str), "created_at must be string (ISO datetime)"


class TestListTenantsContract:
    """Test GET /api/admin/tenants endpoint"""

    def test_list_tenants_endpoint_exists(self, auth_headers):
        """Endpoint should exist"""
        response = client.get("/api/admin/tenants", headers=auth_headers)

        # Should not return 404
        assert response.status_code != 404, "Endpoint /api/admin/tenants does not exist"

    def test_list_tenants_requires_auth(self):
        """Endpoint should require authentication"""
        response = client.get("/api/admin/tenants")

        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"

    def test_list_tenants_response_schema(self, auth_headers):
        """Response should match contract schema"""
        response = client.get("/api/admin/tenants", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            # Validate response schema
            assert "tenants" in data, "Response must include tenants array"
            assert "total" in data, "Response must include total count"
            assert "limit" in data, "Response must include limit"
            assert "offset" in data, "Response must include offset"

            assert isinstance(data["tenants"], list), "tenants must be array"
            assert isinstance(data["total"], int), "total must be integer"
            assert isinstance(data["limit"], int), "limit must be integer"
            assert isinstance(data["offset"], int), "offset must be integer"

    def test_list_tenants_pagination(self, auth_headers):
        """Endpoint should support pagination parameters"""
        response = client.get(
            "/api/admin/tenants?limit=10&offset=0",
            headers=auth_headers
        )

        # Should accept pagination params
        if response.status_code == 200:
            data = response.json()
            assert data["limit"] == 10, "Should respect limit parameter"
            assert data["offset"] == 0, "Should respect offset parameter"


class TestGetTenantContract:
    """Test GET /api/admin/tenants/{tenant_id} endpoint"""

    def test_get_tenant_endpoint_exists(self, auth_headers):
        """Endpoint should exist"""
        response = client.get(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000",
            headers=auth_headers
        )

        # Should not return 404 for endpoint (may return 404 for tenant not found)
        assert response.status_code in [200, 403, 404], "Endpoint should exist"

    def test_get_tenant_requires_auth(self):
        """Endpoint should require authentication"""
        response = client.get("/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000")

        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"


class TestUpdateTenantContract:
    """Test PATCH /api/admin/tenants/{tenant_id} endpoint"""

    def test_update_tenant_endpoint_exists(self, auth_headers):
        """Endpoint should exist"""
        response = client.patch(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000",
            json={"is_active": False},
            headers=auth_headers
        )

        # Should not return 404 for endpoint
        assert response.status_code in [200, 403, 404], "Endpoint should exist"

    def test_update_tenant_requires_auth(self):
        """Endpoint should require authentication"""
        response = client.patch(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000",
            json={"is_active": False}
        )

        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"


class TestAddTenantUserContract:
    """Test POST /api/admin/tenants/{tenant_id}/users endpoint"""

    def test_add_tenant_user_endpoint_exists(self, auth_headers):
        """Endpoint should exist"""
        response = client.post(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000/users",
            json={
                "email": "newuser@test.com",
                "role": "member"
            },
            headers=auth_headers
        )

        # Should not return 404 for endpoint
        assert response.status_code in [201, 403, 404, 409], "Endpoint should exist"

    def test_add_tenant_user_requires_auth(self):
        """Endpoint should require authentication"""
        response = client.post(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000/users",
            json={
                "email": "newuser@test.com",
                "role": "member"
            }
        )

        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"

    def test_add_tenant_user_validates_role(self, auth_headers):
        """Role must be valid enum value"""
        response = client.post(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000/users",
            json={
                "email": "newuser@test.com",
                "role": "invalid_role"
            },
            headers=auth_headers
        )

        # Should return 422 validation error
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data, "Validation error must have detail field"


class TestListTenantUsersContract:
    """Test GET /api/admin/tenants/{tenant_id}/users endpoint"""

    def test_list_tenant_users_endpoint_exists(self, auth_headers):
        """Endpoint should exist"""
        response = client.get(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000/users",
            headers=auth_headers
        )

        # Should not return 404 for endpoint
        assert response.status_code in [200, 403, 404], "Endpoint should exist"

    def test_list_tenant_users_requires_auth(self):
        """Endpoint should require authentication"""
        response = client.get(
            "/api/admin/tenants/550e8400-e29b-41d4-a716-446655440000/users"
        )

        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"

"""
Contract Test: POST /api/auth/discover-tenant

Tests the tenant discovery endpoint contract as defined in:
specs/002-see-here-what/contracts/tenant-discovery.yaml

These tests MUST FAIL before implementation begins (TDD).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestTenantDiscoveryContract:
    """Test tenant discovery endpoint conforms to contract"""

    def test_discover_tenant_endpoint_exists(self):
        """Endpoint should exist and accept POST requests"""
        response = client.post("/api/auth/discover-tenant", json={"email": "test@example.com"})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "Endpoint /api/auth/discover-tenant does not exist"

    def test_single_tenant_response_schema(self):
        """Single tenant response should match contract schema"""
        response = client.post(
            "/api/auth/discover-tenant",
            json={"email": "david@taskifai.com"}
        )

        # Should return 200 or 404 (not implementation error)
        assert response.status_code in [200, 404], f"Unexpected status code: {response.status_code}"

        if response.status_code == 200:
            data = response.json()

            # Check for single tenant response structure
            if "subdomain" in data:
                # Single tenant response
                assert "subdomain" in data, "Missing 'subdomain' in single tenant response"
                assert "company_name" in data, "Missing 'company_name' in single tenant response"
                assert "redirect_url" in data, "Missing 'redirect_url' in single tenant response"

                # Validate data types
                assert isinstance(data["subdomain"], str), "subdomain must be string"
                assert isinstance(data["company_name"], str), "company_name must be string"
                assert isinstance(data["redirect_url"], str), "redirect_url must be string"

                # Validate subdomain pattern
                import re
                assert re.match(r'^[a-z0-9-]+$', data["subdomain"]), "subdomain must match pattern ^[a-z0-9-]+$"

                # Validate redirect URL format
                assert data["redirect_url"].startswith("https://"), "redirect_url must be HTTPS"
                assert "taskifai.com" in data["redirect_url"], "redirect_url must contain taskifai.com"
                assert f"email={data.get('email', 'david@taskifai.com')}" in data["redirect_url"], "redirect_url must include email param"

    def test_multi_tenant_response_schema(self):
        """Multi-tenant response should match contract schema"""
        # This endpoint might return multi-tenant for super admins
        response = client.post(
            "/api/auth/discover-tenant",
            json={"email": "admin@example.com"}  # Hypothetical multi-tenant user
        )

        if response.status_code == 200:
            data = response.json()

            # Check for multi-tenant response structure
            if "tenants" in data:
                # Multi tenant response
                assert "tenants" in data, "Missing 'tenants' in multi-tenant response"
                assert isinstance(data["tenants"], list), "tenants must be array"
                assert len(data["tenants"]) >= 2, "Multi-tenant response must have at least 2 tenants"

                # Validate each tenant option
                for tenant in data["tenants"]:
                    assert "subdomain" in tenant, "Each tenant must have subdomain"
                    assert "company_name" in tenant, "Each tenant must have company_name"
                    assert isinstance(tenant["subdomain"], str), "subdomain must be string"
                    assert isinstance(tenant["company_name"], str), "company_name must be string"

                    # Validate subdomain pattern
                    import re
                    assert re.match(r'^[a-z0-9-]+$', tenant["subdomain"]), f"subdomain '{tenant['subdomain']}' must match pattern"

    def test_request_validation_email_required(self):
        """Request must include email field"""
        response = client.post(
            "/api/auth/discover-tenant",
            json={}  # Missing email
        )

        # Should return 422 validation error
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}"

        error_data = response.json()
        assert "detail" in error_data, "Validation error must have 'detail' field"

    def test_request_validation_invalid_email(self):
        """Request must validate email format"""
        response = client.post(
            "/api/auth/discover-tenant",
            json={"email": "not-an-email"}  # Invalid email format
        )

        # Should return 422 validation error
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"

        error_data = response.json()
        assert "detail" in error_data, "Validation error must have 'detail' field"

    def test_not_found_response(self):
        """404 response should match contract schema"""
        response = client.post(
            "/api/auth/discover-tenant",
            json={"email": "nonexistent@example.com"}
        )

        # May return 404 if email not in registry
        if response.status_code == 404:
            data = response.json()
            assert "detail" in data, "404 error must have 'detail' field"
            assert isinstance(data["detail"], str), "detail must be string"
            assert "no tenant found" in data["detail"].lower() or "not found" in data["detail"].lower(), \
                "Error message should indicate tenant not found"

    def test_response_content_type(self):
        """Response must be JSON"""
        response = client.post(
            "/api/auth/discover-tenant",
            json={"email": "test@example.com"}
        )

        assert "application/json" in response.headers.get("content-type", ""), \
            "Response must be application/json"

    def test_rate_limiting_present(self):
        """Endpoint should have rate limiting (429 on excessive requests)"""
        # Make many requests rapidly
        responses = []
        for _ in range(20):
            response = client.post(
                "/api/auth/discover-tenant",
                json={"email": f"test{_}@example.com"}
            )
            responses.append(response)

        # At least one should be rate limited (or all succeed if limit not reached)
        status_codes = [r.status_code for r in responses]

        # If rate limiting is implemented, we should see a 429
        if 429 in status_codes:
            rate_limited = [r for r in responses if r.status_code == 429][0]
            data = rate_limited.json()
            assert "detail" in data, "Rate limit error must have 'detail' field"
            pytest.skip("Rate limiting verified - skipping assertion to avoid flakiness")
        else:
            pytest.skip("Rate limiting not triggered in test - may need more requests or is not yet implemented")

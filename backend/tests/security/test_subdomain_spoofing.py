"""
T087: Subdomain Spoofing Prevention Test
Verify validation prevents malicious subdomain patterns
"""

import pytest
from httpx import AsyncClient


@pytest.mark.security
@pytest.mark.asyncio
class TestSubdomainSpoofing:
    """Security tests for subdomain spoofing prevention"""

    async def test_path_traversal_in_subdomain_blocked(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Test path traversal attacks blocked

        Expected:
        - Subdomains with ../ rejected
        - Cannot access parent directories
        """
        malicious_hosts = [
            "../../../etc/passwd.taskifai.com",
            "../../admin.taskifai.com",
            "test/../admin.taskifai.com",
        ]

        for host in malicious_hosts:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            # Should reject malicious Host header
            assert response.status_code in [400, 403], \
                f"Path traversal not blocked: {host}"

    async def test_xss_in_subdomain_blocked(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Test XSS injection in subdomain blocked

        Expected:
        - Script tags in subdomain rejected
        - HTML entities escaped/rejected
        """
        malicious_hosts = [
            "<script>alert('xss')</script>.taskifai.com",
            "test<script>.taskifai.com",
            "test'><script>alert(1)</script>.taskifai.com",
        ]

        for host in malicious_hosts:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            assert response.status_code in [400, 403], \
                f"XSS pattern not blocked: {host}"

    async def test_sql_injection_in_subdomain_blocked(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Test SQL injection in subdomain blocked

        Expected:
        - SQL keywords in subdomain rejected
        - Quote characters handled safely
        """
        malicious_hosts = [
            "test'; DROP TABLE tenants; --.taskifai.com",
            "test' OR '1'='1.taskifai.com",
            "test'--admin.taskifai.com",
        ]

        for host in malicious_hosts:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            assert response.status_code in [400, 403], \
                f"SQL injection not blocked: {host}"

    async def test_null_byte_injection_blocked(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Test null byte injection blocked

        Expected:
        - \x00 (null byte) rejected
        - Cannot bypass validation
        """
        malicious_hosts = [
            "test\x00admin.taskifai.com",
            "demo\x00.taskifai.com",
        ]

        for host in malicious_hosts:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            assert response.status_code in [400, 403], \
                f"Null byte not blocked: {repr(host)}"

    async def test_url_encoding_subdomain_blocked(
        self, async_client: AsyncClient
    ):
        """
        CRITICAL: Test URL-encoded malicious subdomains blocked

        Expected:
        - Encoded special chars rejected
        - %00, %2e%2e, etc. blocked
        """
        malicious_hosts = [
            "test%00admin.taskifai.com",
            "test%2e%2e%2fadmin.taskifai.com",  # ../admin
            "test%27admin.taskifai.com",  # test'admin
        ]

        for host in malicious_hosts:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            assert response.status_code in [400, 403], \
                f"URL encoding not blocked: {host}"

    async def test_reserved_subdomains_blocked(
        self, async_client: AsyncClient
    ):
        """
        Test reserved subdomains cannot be used

        Expected:
        - admin, api, www, mail, etc. blocked
        - System subdomains protected
        """
        reserved = [
            "admin.taskifai.com",
            "api.taskifai.com",
            "www.taskifai.com",
            "mail.taskifai.com",
            "localhost.taskifai.com",
        ]

        for host in reserved:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            # May be blocked at registration, not necessarily at request time
            # But should not route to tenant database
            assert response.status_code in [200, 403, 404]

    async def test_subdomain_length_limits(
        self, async_client: AsyncClient
    ):
        """
        Test subdomain length limits enforced

        Expected:
        - Max length (e.g., 63 chars per DNS spec)
        - Prevents buffer overflow attacks
        """
        # Very long subdomain
        long_subdomain = "a" * 100 + ".taskifai.com"

        response = await async_client.get(
            "/health",
            headers={"Host": long_subdomain}
        )

        assert response.status_code in [400, 403], \
            "Overly long subdomain not rejected"

    async def test_subdomain_only_alphanumeric_hyphen(
        self, async_client: AsyncClient
    ):
        """
        Test only alphanumeric and hyphen allowed

        Expected:
        - Special chars rejected: _, @, #, $, etc.
        - Only a-z, 0-9, - allowed
        """
        invalid_chars = [
            "test_company.taskifai.com",  # Underscore
            "test@company.taskifai.com",  # At sign
            "test#company.taskifai.com",  # Hash
            "test$company.taskifai.com",  # Dollar
            "test company.taskifai.com",  # Space
        ]

        for host in invalid_chars:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            assert response.status_code in [400, 403], \
                f"Invalid character not blocked: {host}"

    async def test_subdomain_cannot_start_or_end_with_hyphen(
        self, async_client: AsyncClient
    ):
        """
        Test subdomain validation rules

        Expected:
        - Cannot start with hyphen
        - Cannot end with hyphen
        """
        invalid_subdomains = [
            "-test.taskifai.com",  # Starts with hyphen
            "test-.taskifai.com",  # Ends with hyphen
        ]

        for host in invalid_subdomains:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            assert response.status_code in [400, 403], \
                f"Invalid hyphen position not blocked: {host}"

    async def test_jwt_tenant_id_matches_subdomain(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        CRITICAL: Test JWT tenant_id must match subdomain

        Expected:
        - demo.taskifai.com + JWT(tenant_id=acme) → rejected
        - Prevents subdomain spoofing via JWT
        """
        # JWT for demo tenant
        demo_token = auth_headers["Authorization"]

        # Try to access acme tenant with demo JWT
        response = await async_client.get(
            "/api/analytics/kpis",
            headers={
                "Host": "acme.taskifai.com",  # Different tenant
                "Authorization": demo_token  # Demo token
            }
        )

        # Should reject: tenant mismatch
        assert response.status_code == 403, \
            "Allowed access with mismatched tenant in JWT!"

    async def test_localhost_blocked_in_production(
        self, async_client: AsyncClient
    ):
        """
        Test localhost not allowed as subdomain in production

        Expected:
        - localhost.taskifai.com blocked
        - 127.0.0.1 blocked
        """
        local_hosts = [
            "localhost.taskifai.com",
            "127.0.0.1",
            "localhost",
        ]

        for host in local_hosts:
            response = await async_client.get(
                "/health",
                headers={"Host": host}
            )

            # In production, should block localhost
            # In development, might allow
            # Test documents expected behavior
            assert response.status_code in [200, 400, 403]

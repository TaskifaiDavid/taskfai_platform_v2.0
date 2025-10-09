"""
Security Test: Subdomain Spoofing Prevention

Tests subdomain extraction and validation against malicious inputs.
Verifies defense-in-depth security measures.
"""

import pytest
from app.core.tenant import TenantContextManager


class TestSubdomainSpoofing:
    """Test subdomain extraction against malicious inputs"""

    def test_valid_subdomains(self):
        """Valid subdomains should be extracted correctly"""
        valid_cases = [
            ("customer1.taskifai.com", "customer1"),
            ("demo.taskifai.com", "demo"),
            ("abc-123.taskifai.com", "abc-123"),
            ("test-org.taskifai.com", "test-org"),
        ]

        for hostname, expected in valid_cases:
            result = TenantContextManager.extract_subdomain(hostname)
            assert result == expected, f"Failed for {hostname}"

    def test_path_traversal_attempts(self):
        """Path traversal attempts should be rejected"""
        malicious_cases = [
            "../admin.taskifai.com",
            "../../root.taskifai.com",
        ]

        for hostname in malicious_cases:
            result = TenantContextManager.extract_subdomain(hostname)
            assert result is None, \
                f"Path traversal not blocked: {hostname} → {result}"

    def test_xss_attempts(self):
        """XSS injection attempts should be rejected"""
        malicious_cases = [
            "<script>.taskifai.com",
            "javascript:alert.taskifai.com",
        ]

        for hostname in malicious_cases:
            result = TenantContextManager.extract_subdomain(hostname)
            assert result is None, \
                f"XSS attempt not blocked: {hostname} → {result}"

    def test_special_characters(self):
        """Special characters should be rejected"""
        malicious_cases = [
            "customer1@admin.taskifai.com",
            "customer1#admin.taskifai.com",
            "customer1$.taskifai.com",
        ]

        for hostname in malicious_cases:
            result = TenantContextManager.extract_subdomain(hostname)
            assert result is None, \
                f"Special character not blocked: {hostname} → {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

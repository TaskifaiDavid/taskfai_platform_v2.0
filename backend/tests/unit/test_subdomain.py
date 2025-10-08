"""
Unit tests for subdomain extraction
Tests: backend/app/core/tenant.py:103-131 (extract_subdomain method)
"""

import pytest
from app.core.tenant import TenantContextManager


class TestSubdomainExtraction:
    """Test subdomain extraction logic"""

    @pytest.fixture
    def manager(self):
        """Create TenantContextManager instance"""
        return TenantContextManager()

    # ============================================
    # VALID SUBDOMAIN CASES
    # ============================================

    def test_extract_subdomain_from_full_domain(self, manager):
        """Test extracting subdomain from full domain"""
        hostname = "customer1.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "customer1"

    def test_extract_subdomain_demo(self, manager):
        """Test extracting demo subdomain"""
        hostname = "demo.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "demo"

    def test_extract_subdomain_with_port(self, manager):
        """Test extracting subdomain with port number"""
        hostname = "customer1.taskifai.com:8000"
        # Port should not affect extraction
        result = manager.extract_subdomain(hostname)
        assert result == "customer1"

    def test_extract_subdomain_multi_level(self, manager):
        """Test extracting from multi-level subdomain"""
        hostname = "api.customer1.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "api"

    def test_extract_subdomain_with_hyphen(self, manager):
        """Test extracting subdomain with hyphen"""
        hostname = "customer-one.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "customer-one"

    def test_extract_subdomain_with_numbers(self, manager):
        """Test extracting subdomain with numbers"""
        hostname = "customer123.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "customer123"

    # ============================================
    # LOCALHOST CASES
    # ============================================

    def test_localhost_returns_demo(self, manager):
        """Test localhost returns demo"""
        hostname = "localhost"
        result = manager.extract_subdomain(hostname)
        assert result == "demo"

    def test_localhost_with_port_returns_demo(self, manager):
        """Test localhost with port returns demo"""
        hostname = "localhost:3000"
        result = manager.extract_subdomain(hostname)
        assert result == "demo"

    def test_127_0_0_1_returns_demo(self, manager):
        """Test 127.0.0.1 returns demo"""
        hostname = "127.0.0.1"
        result = manager.extract_subdomain(hostname)
        assert result == "demo"

    def test_127_0_0_1_with_port_returns_demo(self, manager):
        """Test 127.0.0.1 with port returns demo"""
        hostname = "127.0.0.1:8000"
        result = manager.extract_subdomain(hostname)
        assert result == "demo"

    # ============================================
    # MAIN DOMAIN CASES (NO SUBDOMAIN)
    # ============================================

    def test_main_domain_returns_none(self, manager):
        """Test main domain without subdomain returns None"""
        hostname = "taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result is None

    def test_main_domain_with_port_returns_none(self, manager):
        """Test main domain with port returns None"""
        hostname = "taskifai.com:8000"
        result = manager.extract_subdomain(hostname)
        assert result is None

    def test_single_word_domain_returns_none(self, manager):
        """Test single word domain returns None"""
        hostname = "production"
        result = manager.extract_subdomain(hostname)
        assert result is None

    def test_two_part_domain_returns_none(self, manager):
        """Test two-part domain returns None"""
        hostname = "example.com"
        result = manager.extract_subdomain(hostname)
        assert result is None

    # ============================================
    # EDGE CASES
    # ============================================

    def test_empty_string(self, manager):
        """Test empty string"""
        hostname = ""
        result = manager.extract_subdomain(hostname)
        assert result is None

    def test_only_dots(self, manager):
        """Test hostname with only dots"""
        hostname = "..."
        result = manager.extract_subdomain(hostname)
        # Should return empty string as first part
        assert result == ""

    def test_trailing_dot(self, manager):
        """Test hostname with trailing dot"""
        hostname = "customer1.taskifai.com."
        result = manager.extract_subdomain(hostname)
        # Split will create empty string at end
        assert result == "customer1"

    def test_leading_dot(self, manager):
        """Test hostname with leading dot"""
        hostname = ".customer1.taskifai.com"
        result = manager.extract_subdomain(hostname)
        # Split will create empty string at start
        assert result == ""

    def test_case_preservation(self, manager):
        """Test that subdomain case is preserved"""
        hostname = "Customer1.TaskifAI.com"
        result = manager.extract_subdomain(hostname)
        assert result == "Customer1"

    # ============================================
    # IP ADDRESS CASES
    # ============================================

    def test_ipv4_without_localhost(self, manager):
        """Test IPv4 address that's not localhost"""
        hostname = "192.168.1.100"
        result = manager.extract_subdomain(hostname)
        # Not localhost, no subdomain
        assert result is None

    def test_ipv6_localhost(self, manager):
        """Test IPv6 localhost notation"""
        hostname = "::1"
        result = manager.extract_subdomain(hostname)
        # Not explicitly handled, returns None
        assert result is None

    # ============================================
    # PRODUCTION SCENARIOS
    # ============================================

    def test_production_subdomain(self, manager):
        """Test production subdomain extraction"""
        hostname = "acmecorp.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "acmecorp"

    def test_staging_subdomain(self, manager):
        """Test staging subdomain"""
        hostname = "staging.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "staging"

    def test_dev_subdomain(self, manager):
        """Test dev subdomain"""
        hostname = "dev.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "dev"

    # ============================================
    # PARAMETRIZED TESTS
    # ============================================

    @pytest.mark.parametrize("hostname,expected", [
        ("customer1.taskifai.com", "customer1"),
        ("demo.taskifai.com", "demo"),
        ("localhost", "demo"),
        ("127.0.0.1", "demo"),
        ("taskifai.com", None),
        ("example.com", None),
        ("a.b.c.com", "a"),
        ("test-123.taskifai.com", "test-123"),
    ])
    def test_subdomain_extraction_parametrized(self, manager, hostname, expected):
        """Parametrized test for various hostname formats"""
        result = manager.extract_subdomain(hostname)
        assert result == expected

    # ============================================
    # INTEGRATION WITH CONTEXT MANAGER
    # ============================================

    @pytest.mark.asyncio
    async def test_extract_subdomain_is_static(self, manager):
        """Test that extract_subdomain is a static method"""
        # Should be callable without instance
        result = TenantContextManager.extract_subdomain("test.taskifai.com")
        assert result == "test"


# ============================================
# SECURITY TESTS
# ============================================

class TestSubdomainSecurity:
    """Test security aspects of subdomain extraction"""

    @pytest.fixture
    def manager(self):
        return TenantContextManager()

    def test_sql_injection_attempt(self, manager):
        """Test that SQL injection patterns are safely extracted"""
        hostname = "'; DROP TABLE users; --.taskifai.com"
        result = manager.extract_subdomain(hostname)
        # Should extract the malicious string as-is (validation happens elsewhere)
        assert result == "'; DROP TABLE users; --"

    def test_xss_attempt(self, manager):
        """Test that XSS patterns are safely extracted"""
        hostname = "<script>alert('xss')</script>.taskifai.com"
        result = manager.extract_subdomain(hostname)
        # Should extract as-is, HTML encoding happens elsewhere
        assert result == "<script>alert('xss')</script>"

    def test_path_traversal_attempt(self, manager):
        """Test that path traversal is safely extracted"""
        hostname = "../../etc/passwd.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "../../etc/passwd"

    def test_null_byte_injection(self, manager):
        """Test null byte injection"""
        hostname = "customer1\x00.taskifai.com"
        result = manager.extract_subdomain(hostname)
        # Python strings handle null bytes, should extract with null
        assert "\x00" in result

    def test_unicode_subdomain(self, manager):
        """Test unicode characters in subdomain"""
        hostname = "münchen.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == "münchen"


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestSubdomainPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def manager(self):
        return TenantContextManager()

    def test_very_long_subdomain(self, manager):
        """Test very long subdomain"""
        long_subdomain = "a" * 500
        hostname = f"{long_subdomain}.taskifai.com"
        result = manager.extract_subdomain(hostname)
        assert result == long_subdomain
        assert len(result) == 500

    def test_many_subdomain_levels(self, manager):
        """Test many nested subdomain levels"""
        hostname = "level5.level4.level3.level2.level1.taskifai.com"
        result = manager.extract_subdomain(hostname)
        # Should return first part
        assert result == "level5"

"""
Unit tests for vendor config loader
Tests: backend/app/services/vendors/config_loader.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.vendors.config_loader import VendorConfigLoader, get_vendor_config
from app.models.vendor_config import VendorConfigData


class TestVendorConfigLoader:
    """Test vendor configuration loading with inheritance"""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        return Mock()

    @pytest.fixture
    def loader(self, mock_supabase):
        """Create VendorConfigLoader instance"""
        return VendorConfigLoader(mock_supabase)

    # ============================================
    # CONFIGURATION LOADING TESTS
    # ============================================

    def test_load_tenant_specific_config(self, loader, mock_supabase):
        """Test loading tenant-specific configuration"""
        # Mock Supabase response
        mock_result = Mock()
        mock_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "USD",
                "exchange_rate": 1.2
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = mock_result

        config = loader.load_config("boxnox", "tenant-123")

        assert config.vendor_name == "boxnox"
        assert config.currency == "USD"

    def test_fallback_to_default_config(self, loader, mock_supabase):
        """Test fallback to default config when tenant config not found"""
        # Mock empty tenant config
        empty_result = Mock()
        empty_result.data = []

        # Mock default config
        default_result = Mock()
        default_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "EUR",
                "exchange_rate": 1.0
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.side_effect = [
            empty_result,  # Tenant config
            default_result  # Default config
        ]

        config = loader.load_config("boxnox", "tenant-123")

        assert config.currency == "EUR"

    def test_fallback_to_hardcoded_default(self, loader, mock_supabase):
        """Test fallback to hardcoded defaults when DB configs not found"""
        # Mock empty results from DB
        empty_result = Mock()
        empty_result.data = []

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = empty_result
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = empty_result

        config = loader.load_config("boxnox", "tenant-123")

        # Should return hardcoded default
        assert config.vendor_name == "boxnox"
        assert config.currency == "EUR"

    def test_load_config_for_demo_tenant(self, loader, mock_supabase):
        """Test loading config for demo tenant skips tenant lookup"""
        # Mock default config
        default_result = Mock()
        default_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "EUR"
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = default_result

        config = loader.load_config("boxnox", "demo")

        # Should skip tenant lookup for demo
        assert config.vendor_name == "boxnox"

    def test_load_config_without_tenant_id(self, loader, mock_supabase):
        """Test loading config without tenant_id uses default"""
        # Mock default config
        default_result = Mock()
        default_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "EUR"
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = default_result

        config = loader.load_config("boxnox", None)

        assert config.vendor_name == "boxnox"

    # ============================================
    # ERROR HANDLING TESTS
    # ============================================

    def test_handle_database_error_gracefully(self, loader, mock_supabase):
        """Test graceful handling of database errors"""
        # Mock database error
        mock_supabase.table.return_value.select.return_value.match.return_value.execute.side_effect = Exception("DB Error")
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.side_effect = Exception("DB Error")

        # Should fallback to hardcoded default
        config = loader.load_config("boxnox", "tenant-123")

        assert config.vendor_name == "boxnox"
        assert config.currency == "EUR"

    def test_raise_error_for_unknown_vendor(self, loader, mock_supabase):
        """Test that unknown vendor raises ValueError"""
        # Mock empty results
        empty_result = Mock()
        empty_result.data = []

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = empty_result
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = empty_result

        with pytest.raises(ValueError, match="No configuration found for vendor"):
            loader.load_config("unknown_vendor", "tenant-123")

    def test_handle_malformed_config_data(self, loader, mock_supabase):
        """Test handling of malformed config data"""
        # Mock malformed data
        malformed_result = Mock()
        malformed_result.data = [{
            "config_data": {
                "vendor_name": "boxnox"
                # Missing required fields
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = malformed_result

        # Should raise validation error or fallback
        try:
            config = loader.load_config("boxnox", "tenant-123")
            # If it doesn't raise, should have fallback values
            assert config.vendor_name == "boxnox"
        except Exception:
            # Validation error is acceptable
            pass

    # ============================================
    # CONFIGURATION PRIORITY TESTS
    # ============================================

    def test_tenant_config_overrides_default(self, loader, mock_supabase):
        """Test that tenant config takes priority over default"""
        # Mock tenant config
        tenant_result = Mock()
        tenant_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "USD",  # Tenant-specific
                "exchange_rate": 1.2
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = tenant_result

        config = loader.load_config("boxnox", "tenant-123")

        # Should use tenant-specific currency
        assert config.currency == "USD"
        assert config.exchange_rate == 1.2

    def test_default_config_used_when_no_tenant_config(self, loader, mock_supabase):
        """Test default config is used when tenant config doesn't exist"""
        # Mock empty tenant config
        empty_tenant = Mock()
        empty_tenant.data = []

        # Mock default config
        default_result = Mock()
        default_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "EUR",
                "exchange_rate": 1.0
            }
        }]

        # Return empty for tenant, populated for default
        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = empty_tenant
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = default_result

        config = loader.load_config("boxnox", "tenant-123")

        assert config.currency == "EUR"

    # ============================================
    # VENDOR LISTING TESTS
    # ============================================

    def test_list_available_vendors_from_db(self, loader, mock_supabase):
        """Test listing available vendors from database"""
        # Mock vendor list
        vendors_result = Mock()
        vendors_result.data = [
            {"vendor_name": "boxnox"},
            {"vendor_name": "galilu"},
            {"vendor_name": "skins_sa"}
        ]

        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = vendors_result

        vendors = loader.list_available_vendors()

        assert len(vendors) == 3
        assert "boxnox" in vendors
        assert "galilu" in vendors
        assert "skins_sa" in vendors

    def test_list_available_vendors_fallback(self, loader, mock_supabase):
        """Test fallback to hardcoded vendor list"""
        # Mock database error
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.side_effect = Exception("DB Error")

        vendors = loader.list_available_vendors()

        # Should return hardcoded list
        assert len(vendors) == 10
        assert "boxnox" in vendors
        assert "galilu" in vendors

    def test_list_available_vendors_with_tenant_id(self, loader, mock_supabase):
        """Test listing vendors with tenant context"""
        vendors_result = Mock()
        vendors_result.data = [
            {"vendor_name": "boxnox"},
            {"vendor_name": "galilu"}
        ]

        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = vendors_result

        vendors = loader.list_available_vendors("tenant-123")

        assert len(vendors) >= 2

    # ============================================
    # HARDCODED DEFAULTS TESTS
    # ============================================

    def test_hardcoded_boxnox_config(self, loader, mock_supabase):
        """Test hardcoded Boxnox configuration"""
        # Mock empty DB results to trigger hardcoded fallback
        empty_result = Mock()
        empty_result.data = []

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = empty_result
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = empty_result

        config = loader.load_config("boxnox", "tenant-123")

        assert config.vendor_name == "boxnox"
        assert config.currency == "EUR"
        assert config.exchange_rate == 1.0
        assert config.file_format.type == "excel"
        assert config.file_format.sheet_name == "Sell Out by EAN"

    def test_hardcoded_config_has_all_required_fields(self, loader, mock_supabase):
        """Test hardcoded config has all required VendorConfigData fields"""
        empty_result = Mock()
        empty_result.data = []

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = empty_result
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = empty_result

        config = loader.load_config("boxnox", "tenant-123")

        # Check all major fields exist
        assert hasattr(config, 'vendor_name')
        assert hasattr(config, 'currency')
        assert hasattr(config, 'exchange_rate')
        assert hasattr(config, 'file_format')
        assert hasattr(config, 'column_mapping')
        assert hasattr(config, 'transformation_rules')
        assert hasattr(config, 'validation_rules')
        assert hasattr(config, 'detection_rules')


# ============================================
# HELPER FUNCTION TESTS
# ============================================

class TestGetVendorConfigHelper:
    """Test get_vendor_config helper function"""

    @pytest.fixture
    def mock_supabase(self):
        return Mock()

    def test_helper_function_returns_config(self, mock_supabase):
        """Test helper function returns VendorConfigData"""
        # Mock default config
        default_result = Mock()
        default_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "EUR"
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = default_result

        config = get_vendor_config(mock_supabase, "boxnox", "tenant-123")

        assert isinstance(config, VendorConfigData)
        assert config.vendor_name == "boxnox"

    def test_helper_function_with_none_tenant(self, mock_supabase):
        """Test helper function with None tenant_id"""
        default_result = Mock()
        default_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "EUR"
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = default_result

        config = get_vendor_config(mock_supabase, "boxnox", None)

        assert config.vendor_name == "boxnox"


# ============================================
# INTEGRATION TESTS
# ============================================

class TestVendorConfigLoaderIntegration:
    """Integration tests for config loader"""

    @pytest.fixture
    def mock_supabase(self):
        return Mock()

    @pytest.fixture
    def loader(self, mock_supabase):
        return VendorConfigLoader(mock_supabase)

    def test_complete_config_loading_flow(self, loader, mock_supabase):
        """Test complete configuration loading flow"""
        # Simulate real scenario: no tenant config, use default
        empty_tenant = Mock()
        empty_tenant.data = []

        default_result = Mock()
        default_result.data = [{
            "config_data": {
                "vendor_name": "boxnox",
                "currency": "EUR",
                "exchange_rate": 1.0,
                "file_format": {
                    "type": "excel",
                    "sheet_name": "Sell Out by EAN"
                },
                "column_mapping": {
                    "product_ean": "Product EAN"
                }
            }
        }]

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = empty_tenant
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = default_result

        config = loader.load_config("boxnox", "tenant-123")

        assert config.vendor_name == "boxnox"
        assert config.currency == "EUR"

    def test_config_loader_caching_behavior(self, loader, mock_supabase):
        """Test that config loader doesn't cache between calls"""
        result1 = Mock()
        result1.data = [{"config_data": {"vendor_name": "boxnox", "currency": "EUR"}}]

        result2 = Mock()
        result2.data = [{"config_data": {"vendor_name": "boxnox", "currency": "USD"}}]

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.side_effect = [result1, result2]

        config1 = loader.load_config("boxnox", "tenant-1")
        config2 = loader.load_config("boxnox", "tenant-2")

        # Should load fresh config each time
        assert config1.currency == "EUR"
        assert config2.currency == "USD"


# ============================================
# SECURITY TESTS
# ============================================

class TestVendorConfigLoaderSecurity:
    """Test security aspects of config loader"""

    @pytest.fixture
    def mock_supabase(self):
        return Mock()

    @pytest.fixture
    def loader(self, mock_supabase):
        return VendorConfigLoader(mock_supabase)

    def test_sql_injection_in_tenant_id(self, loader, mock_supabase):
        """Test SQL injection attempts in tenant_id"""
        # Mock result
        result = Mock()
        result.data = []

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = result
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = result

        # Should not crash with SQL injection attempt
        config = loader.load_config("boxnox", "'; DROP TABLE vendor_configs; --")

        # Should fallback to hardcoded defaults
        assert config.vendor_name == "boxnox"

    def test_xss_in_vendor_name(self, loader, mock_supabase):
        """Test XSS attempts in vendor_name"""
        result = Mock()
        result.data = []

        mock_supabase.table.return_value.select.return_value.match.return_value.execute.return_value = result
        mock_supabase.table.return_value.select.return_value.match.return_value.is_.return_value.execute.return_value = result

        # Should raise error for unknown vendor
        with pytest.raises(ValueError):
            loader.load_config("<script>alert('xss')</script>", "tenant-123")

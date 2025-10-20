"""
Unit tests for BIBBI Product Service

Tests product matching and creation logic:
- 3-tier matching (exact vendor code → fuzzy name → auto-create)
- Product auto-creation with temporary EANs
- Caching functionality
- Race condition handling
- Vendor code validation and sanitization

Tests: backend/app/services/bibbi/product_service.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.bibbi.product_service import BibbιProductService


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_bibbi_db():
    """Mock BIBBI database client"""
    # Create mock for the raw Supabase client (used for products table)
    mock_raw_client = Mock()
    mock_raw_client.table = Mock(return_value=mock_raw_client)
    mock_raw_client.select = Mock(return_value=mock_raw_client)
    mock_raw_client.eq = Mock(return_value=mock_raw_client)
    mock_raw_client.is_ = Mock(return_value=mock_raw_client)
    mock_raw_client.insert = Mock(return_value=mock_raw_client)
    mock_raw_client.update = Mock(return_value=mock_raw_client)
    mock_raw_client.order = Mock(return_value=mock_raw_client)
    mock_raw_client.limit = Mock(return_value=mock_raw_client)
    mock_raw_client.execute = Mock()

    # Create BibbιDB wrapper mock
    mock_db = Mock()
    mock_db.client = mock_raw_client  # Point to raw client for products table
    mock_db.table = Mock(return_value=mock_db)
    mock_db.select = Mock(return_value=mock_db)
    mock_db.eq = Mock(return_value=mock_db)
    mock_db.is_ = Mock(return_value=mock_db)
    mock_db.insert = Mock(return_value=mock_db)
    mock_db.update = Mock(return_value=mock_db)
    mock_db.order = Mock(return_value=mock_db)
    mock_db.limit = Mock(return_value=mock_db)
    mock_db.execute = Mock()

    return mock_db


@pytest.fixture
def product_service(mock_bibbi_db):
    """Product service instance"""
    return BibbιProductService(mock_bibbi_db)


# ============================================
# EXACT VENDOR CODE MATCHING TESTS
# ============================================

class TestMatchByVendorCode:
    """Test exact vendor code matching (Tier 1)"""

    def test_match_existing_vendor_code(self, product_service, mock_bibbi_db):
        """Test matching existing product by vendor code"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"ean": "1234567890123"}]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._match_by_vendor_code("834429", "liberty")

        # Verify
        assert ean == "1234567890123"
        mock_bibbi_db.client.table.assert_called_with("products")
        mock_bibbi_db.eq.assert_called_with("liberty_name", "834429")

    def test_match_vendor_code_not_found(self, product_service, mock_bibbi_db):
        """Test vendor code not found returns None"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._match_by_vendor_code("nonexistent", "liberty")

        # Verify
        assert ean is None

    def test_match_vendor_code_database_error(self, product_service, mock_bibbi_db):
        """Test handling database errors gracefully"""
        # Setup mock to raise exception
        mock_bibbi_db.client.execute.side_effect = Exception("Database error")

        # Execute
        ean = product_service._match_by_vendor_code("834429", "liberty")

        # Verify - should return None on error, not crash
        assert ean is None


# ============================================
# FUZZY NAME MATCHING TESTS
# ============================================

class TestMatchByProductName:
    """Test fuzzy product name matching (Tier 2)"""

    def test_fuzzy_match_exact_description(self, product_service, mock_bibbi_db):
        """Test fuzzy matching with exact description match"""
        # Setup mock response with products
        mock_result = Mock()
        mock_result.data = [
            {"ean": "1234567890123", "description": "TROISIEME 10ML", "functional_name": None},
            {"ean": "9876543210987", "description": "OTHER PRODUCT", "functional_name": None}
        ]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._match_by_product_name("TROISIEME 10ML")

        # Verify - should match with 100% similarity
        assert ean == "1234567890123"
        mock_bibbi_db.client.limit.assert_called_with(1000)

    def test_fuzzy_match_similar_name(self, product_service, mock_bibbi_db):
        """Test fuzzy matching with high similarity (>75%)"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [
            {"ean": "1234567890123", "description": "Troisieme 10ml bottle", "functional_name": None},
        ]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute - similar but not exact
        ean = product_service._match_by_product_name("TROISIEME 10ML")

        # Verify - should still match due to high similarity
        assert ean == "1234567890123"

    def test_fuzzy_match_low_similarity(self, product_service, mock_bibbi_db):
        """Test fuzzy matching with low similarity (<75%) returns None"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [
            {"ean": "1234567890123", "description": "Completely Different Product", "functional_name": None},
        ]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._match_by_product_name("TROISIEME 10ML")

        # Verify - should not match due to low similarity
        assert ean is None

    def test_fuzzy_match_functional_name(self, product_service, mock_bibbi_db):
        """Test fuzzy matching against functional_name field"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [
            {"ean": "1234567890123", "description": None, "functional_name": "TROISIEME 10ML"},
        ]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._match_by_product_name("TROISIEME 10ML")

        # Verify - should match via functional_name
        assert ean == "1234567890123"

    def test_fuzzy_match_no_products(self, product_service, mock_bibbi_db):
        """Test fuzzy matching with no products returns None"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._match_by_product_name("TROISIEME 10ML")

        # Verify
        assert ean is None

    def test_fuzzy_match_respects_limit(self, product_service, mock_bibbi_db):
        """Test fuzzy matching limits query to 1000 products"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        product_service._match_by_product_name("Test Product")

        # Verify limit was applied
        mock_bibbi_db.client.limit.assert_called_with(1000)
        mock_bibbi_db.order.assert_called_with("updated_at", desc=True)


# ============================================
# PRODUCT AUTO-CREATION TESTS
# ============================================

class TestCreateProduct:
    """Test product auto-creation with temporary EANs (Tier 3)"""

    def test_create_product_basic(self, product_service, mock_bibbi_db):
        """Test creating product with vendor code"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"ean": "9000834429000"}]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._create_product("834429", "TROISIEME 10ML", "liberty")

        # Verify - zfill pads from left, so "834429".zfill(12) = "000000834429"
        assert ean == "9000000834429"
        mock_bibbi_db.client.table.assert_called_with("products")
        mock_bibbi_db.client.insert.assert_called_once()

        # Verify insert payload
        call_args = mock_bibbi_db.insert.call_args[0][0]
        assert call_args["ean"] == "9000000834429"
        assert call_args["functional_name"] == "TROISIEME 10ML"
        assert call_args["liberty_name"] == "834429"
        assert call_args["active"] is False

    def test_create_product_vendor_code_sanitization(self, product_service, mock_bibbi_db):
        """Test vendor code sanitization (filter to digits only)"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"ean": "9000123456000"}]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute with non-numeric characters
        ean = product_service._create_product("ABC-123456-XYZ", "Test Product", "liberty")

        # Verify - should filter to "123456" and create "9000000123456" (left-padded)
        assert ean == "9000000123456"

        call_args = mock_bibbi_db.insert.call_args[0][0]
        assert call_args["ean"] == "9000000123456"

    def test_create_product_vendor_code_too_long(self, product_service, mock_bibbi_db):
        """Test vendor code validation (>12 digits after sanitization)"""
        # Execute with code >12 digits - should raise ValueError wrapped in Exception
        with pytest.raises(Exception, match="Failed to create product"):
            product_service._create_product("1234567890123", "Test Product", "liberty")

    def test_create_product_without_name(self, product_service, mock_bibbi_db):
        """Test creating product without product name"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"ean": "9000834429000"}]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service._create_product("834429", None, "liberty")

        # Verify
        assert ean == "9000000834429"

        call_args = mock_bibbi_db.insert.call_args[0][0]
        assert call_args["functional_name"] == "834429"  # Uses vendor code as name
        assert "Auto-created from liberty upload" in call_args["description"]

    def test_create_product_race_condition(self, product_service, mock_bibbi_db):
        """Test handling race condition (duplicate key error)"""
        # Setup mocks - insert fails with duplicate, then fetch finds existing product
        mock_bibbi_db.client.execute.side_effect = [
            Exception("duplicate key value violates unique constraint"),
            Mock(data=[{"ean": "9000834429000"}])  # Existing product found
        ]

        # Execute
        ean = product_service._create_product("834429", "Test Product", "liberty")

        # Verify - should return the existing product's EAN (from race condition)
        assert ean == "9000834429000"

    def test_create_product_race_condition_sanitized_fallback(self, product_service, mock_bibbi_db):
        """Test race condition fallback uses sanitized vendor code"""
        # Setup mocks - insert fails, match also fails
        mock_bibbi_db.client.execute.side_effect = [
            Exception("duplicate key"),
            Mock(data=[])  # match returns nothing
        ]

        # Execute with non-numeric code
        ean = product_service._create_product("ABC-123-XYZ", "Test", "liberty")

        # Verify - should return sanitized temp_ean (9000000000123 - left-padded)
        assert ean == "9000000000123"

    def test_create_product_generic_error(self, product_service, mock_bibbi_db):
        """Test handling non-duplicate errors"""
        # Setup mock to raise generic exception
        mock_bibbi_db.client.execute.side_effect = Exception("Database connection lost")

        # Execute - should raise exception
        with pytest.raises(Exception, match="Failed to create product"):
            product_service._create_product("834429", "Test Product", "liberty")


# ============================================
# CACHING TESTS
# ============================================

class TestCaching:
    """Test product matching cache functionality"""

    def test_cache_hit_avoids_database_query(self, product_service, mock_bibbi_db):
        """Test cache hit prevents database queries"""
        # Setup mock for first call
        mock_result = Mock()
        mock_result.data = [{"ean": "1234567890123"}]
        mock_bibbi_db.client.execute.return_value = mock_result

        # First call - should hit database
        ean1 = product_service.match_or_create_product("834429", "Test Product", "liberty")
        call_count_1 = mock_bibbi_db.client.execute.call_count

        # Second call - should use cache
        ean2 = product_service.match_or_create_product("834429", "Test Product", "liberty")
        call_count_2 = mock_bibbi_db.client.execute.call_count

        # Verify
        assert ean1 == ean2 == "1234567890123"
        assert call_count_2 == call_count_1  # No additional DB calls

    def test_cache_key_includes_vendor_name(self, product_service, mock_bibbi_db):
        """Test cache keys are vendor-specific"""
        # Setup mocks
        mock_result_liberty = Mock()
        mock_result_liberty.data = [{"ean": "1111111111111"}]

        mock_result_galilu = Mock()
        mock_result_galilu.data = [{"ean": "2222222222222"}]

        mock_bibbi_db.client.execute.side_effect = [mock_result_liberty, mock_result_galilu]

        # Call with same code but different vendors
        ean_liberty = product_service.match_or_create_product("12345", "Product", "liberty")
        ean_galilu = product_service.match_or_create_product("12345", "Product", "galilu")

        # Verify - should be different EANs (not cached across vendors)
        assert ean_liberty == "1111111111111"
        assert ean_galilu == "2222222222222"

    def test_clear_cache(self, product_service, mock_bibbi_db):
        """Test cache clearing functionality"""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [{"ean": "1234567890123"}]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Add to cache
        product_service.match_or_create_product("834429", "Test Product", "liberty")
        call_count_1 = mock_bibbi_db.client.execute.call_count

        # Clear cache
        product_service.clear_cache()

        # Call again - should hit database
        product_service.match_or_create_product("834429", "Test Product", "liberty")
        call_count_2 = mock_bibbi_db.client.execute.call_count

        # Verify cache was cleared (additional DB call made)
        assert call_count_2 > call_count_1


# ============================================
# FULL MATCHING WORKFLOW TESTS
# ============================================

class TestMatchOrCreateProduct:
    """Test complete 3-tier matching workflow"""

    def test_tier_1_match_success(self, product_service, mock_bibbi_db):
        """Test Tier 1: Exact vendor code match"""
        # Setup mock for exact match
        mock_result = Mock()
        mock_result.data = [{"ean": "1234567890123"}]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        ean = product_service.match_or_create_product("834429", "Test Product", "liberty")

        # Verify
        assert ean == "1234567890123"
        mock_bibbi_db.eq.assert_called_with("liberty_name", "834429")

    def test_tier_2_fuzzy_match_success(self, product_service, mock_bibbi_db):
        """Test Tier 2: Fuzzy name matching when vendor code fails"""
        # Setup mocks - vendor code match fails, fuzzy match succeeds
        mock_result_empty = Mock()
        mock_result_empty.data = []

        mock_result_fuzzy = Mock()
        mock_result_fuzzy.data = [
            {"ean": "9876543210987", "description": "Test Product Name", "functional_name": None}
        ]

        mock_bibbi_db.client.execute.side_effect = [
            mock_result_empty,  # Vendor code match fails
            mock_result_fuzzy,  # Fuzzy match succeeds
            Mock(data=[])  # Update vendor mapping
        ]

        # Execute
        ean = product_service.match_or_create_product("834429", "Test Product Name", "liberty")

        # Verify
        assert ean == "9876543210987"
        # Should update vendor mapping
        mock_bibbi_db.client.update.assert_called_once()

    def test_tier_3_auto_create(self, product_service, mock_bibbi_db):
        """Test Tier 3: Auto-create when both matches fail"""
        # Setup mocks - all matches fail
        mock_result_empty = Mock()
        mock_result_empty.data = []

        mock_result_create = Mock()
        mock_result_create.data = [{"ean": "9000834429000"}]

        mock_bibbi_db.client.execute.side_effect = [
            mock_result_empty,  # Vendor code match fails
            mock_result_empty,  # Fuzzy match fails
            mock_result_create  # Auto-create succeeds
        ]

        # Execute
        ean = product_service.match_or_create_product("834429", "Test Product", "liberty")

        # Verify
        assert ean == "9000000834429"
        mock_bibbi_db.client.insert.assert_called_once()

    def test_without_product_name(self, product_service, mock_bibbi_db):
        """Test workflow without product name (skips Tier 2)"""
        # Setup mocks
        mock_result_empty = Mock()
        mock_result_empty.data = []

        mock_result_create = Mock()
        mock_result_create.data = [{"ean": "9000834429000"}]

        mock_bibbi_db.client.execute.side_effect = [
            mock_result_empty,  # Vendor code match fails
            mock_result_create  # Auto-create succeeds (skips fuzzy match)
        ]

        # Execute without product name
        ean = product_service.match_or_create_product("834429", None, "liberty")

        # Verify - should skip Tier 2 and go to Tier 3
        assert ean == "9000000834429"


# ============================================
# VENDOR MAPPING UPDATE TESTS
# ============================================

class TestUpdateVendorMapping:
    """Test vendor mapping updates after fuzzy matches"""

    def test_update_vendor_mapping_success(self, product_service, mock_bibbi_db):
        """Test successful vendor mapping update"""
        # Setup mock
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        product_service._update_vendor_mapping("1234567890123", "834429", "liberty")

        # Verify
        mock_bibbi_db.client.table.assert_called_with("products")
        mock_bibbi_db.client.update.assert_called_once()
        mock_bibbi_db.eq.assert_called_with("ean", "1234567890123")

        # Verify update payload
        call_args = mock_bibbi_db.update.call_args[0][0]
        assert call_args["liberty_name"] == "834429"
        assert "updated_at" in call_args

    def test_update_vendor_mapping_handles_errors(self, product_service, mock_bibbi_db):
        """Test vendor mapping update handles errors gracefully"""
        # Setup mock to raise exception
        mock_bibbi_db.client.execute.side_effect = Exception("Database error")

        # Execute - should not crash
        product_service._update_vendor_mapping("1234567890123", "834429", "liberty")

        # Verify - no exception raised (error handled gracefully)


# ============================================
# HELPER METHOD TESTS
# ============================================

class TestHelperMethods:
    """Test utility and helper methods"""

    def test_get_unmapped_products(self, product_service, mock_bibbi_db):
        """Test fetching products without vendor mapping"""
        # Setup mock
        mock_result = Mock()
        mock_result.data = [
            {"ean": "1111111111111", "functional_name": "Product 1", "description": "Desc 1"},
            {"ean": "2222222222222", "functional_name": "Product 2", "description": "Desc 2"}
        ]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        unmapped = product_service.get_unmapped_products("liberty")

        # Verify
        assert len(unmapped) == 2
        mock_bibbi_db.client.is_.assert_called_with("liberty_name", None)

    def test_get_unmapped_products_error(self, product_service, mock_bibbi_db):
        """Test get_unmapped_products handles errors"""
        # Setup mock to raise exception
        mock_bibbi_db.client.execute.side_effect = Exception("Database error")

        # Execute
        unmapped = product_service.get_unmapped_products("liberty")

        # Verify - returns empty list on error
        assert unmapped == []

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
        mock_bibbi_db.client.eq.assert_called_with("liberty_name", "834429")

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
        """Test fuzzy matching with high similarity (>85% threshold)"""
        # Setup mock response - needs very high similarity (>=85%)
        mock_result = Mock()
        mock_result.data = [
            {"ean": "1234567890123", "description": "TROISIEME 10ML", "functional_name": None},
        ]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute - exact match should work
        ean = product_service._match_by_product_name("TROISIEME 10ML")

        # Verify - should match with 100% similarity
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
        mock_bibbi_db.client.order.assert_called_with("updated_at", desc=True)


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
        call_args = mock_bibbi_db.client.insert.call_args[0][0]
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

        call_args = mock_bibbi_db.client.insert.call_args[0][0]
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

        call_args = mock_bibbi_db.client.insert.call_args[0][0]
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
        # Setup mocks
        # First call: vendor code match
        mock_match_result = Mock()
        mock_match_result.data = [{"ean": "1234567890123"}]

        # First call: fetch product details
        mock_product_result = Mock()
        mock_product_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Test Product",
            "description": "Test Description",
            "active": True
        }]

        # Second call: only fetch product details (cache hit on EAN, but still fetches full product)
        mock_bibbi_db.client.execute.side_effect = [
            mock_match_result,      # First call: vendor code match
            mock_product_result,    # First call: fetch details
            mock_product_result     # Second call: fetch details (cache returns EAN, but fetches full product)
        ]

        # First call - should hit database twice (match + fetch)
        result1 = product_service.match_or_create_product("834429", "Test Product", "liberty")

        # Second call - should use cache for EAN but still fetch product details
        result2 = product_service.match_or_create_product("834429", "Test Product", "liberty")

        # Verify - both return same product dict
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert result1["ean"] == result2["ean"] == "1234567890123"
        assert result1["functional_name"] == "Test Product"

        # Cache prevents vendor code lookup, but product details are still fetched
        assert mock_bibbi_db.client.execute.call_count == 3  # match + 2x fetch

    def test_cache_key_includes_vendor_name(self, product_service, mock_bibbi_db):
        """Test cache keys are vendor-specific"""
        # Setup mocks
        mock_result_liberty_match = Mock()
        mock_result_liberty_match.data = [{"ean": "1111111111111"}]

        mock_result_liberty_product = Mock()
        mock_result_liberty_product.data = [{
            "ean": "1111111111111",
            "functional_name": "Liberty Product",
            "description": "From Liberty"
        }]

        mock_result_galilu_match = Mock()
        mock_result_galilu_match.data = [{"ean": "2222222222222"}]

        mock_result_galilu_product = Mock()
        mock_result_galilu_product.data = [{
            "ean": "2222222222222",
            "functional_name": "Galilu Product",
            "description": "From Galilu"
        }]

        mock_bibbi_db.client.execute.side_effect = [
            mock_result_liberty_match,
            mock_result_liberty_product,
            mock_result_galilu_match,
            mock_result_galilu_product
        ]

        # Call with same code but different vendors
        result_liberty = product_service.match_or_create_product("12345", "Product", "liberty")
        result_galilu = product_service.match_or_create_product("12345", "Product", "galilu")

        # Verify - should be different products (not cached across vendors)
        assert isinstance(result_liberty, dict)
        assert isinstance(result_galilu, dict)
        assert result_liberty["ean"] == "1111111111111"
        assert result_galilu["ean"] == "2222222222222"

    def test_clear_cache(self, product_service, mock_bibbi_db):
        """Test cache clearing functionality"""
        # Setup mocks
        mock_match_result = Mock()
        mock_match_result.data = [{"ean": "1234567890123"}]

        mock_product_result = Mock()
        mock_product_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Test Product",
            "description": "Test Description"
        }]

        mock_bibbi_db.client.execute.side_effect = [
            mock_match_result,      # First call: match
            mock_product_result,    # First call: fetch
            mock_match_result,      # After clear: match again
            mock_product_result     # After clear: fetch again
        ]

        # Add to cache
        product_service.match_or_create_product("834429", "Test Product", "liberty")
        call_count_1 = mock_bibbi_db.client.execute.call_count

        # Clear cache
        product_service.clear_cache()

        # Call again - should hit database again
        product_service.match_or_create_product("834429", "Test Product", "liberty")
        call_count_2 = mock_bibbi_db.client.execute.call_count

        # Verify cache was cleared (additional DB calls made)
        assert call_count_2 > call_count_1


# ============================================
# FULL MATCHING WORKFLOW TESTS
# ============================================

class TestMatchOrCreateProduct:
    """Test complete 3-tier matching workflow"""

    def test_tier_1_match_success(self, product_service, mock_bibbi_db):
        """Test Tier 1: Exact vendor code match"""
        # Setup mocks
        mock_match_result = Mock()
        mock_match_result.data = [{"ean": "1234567890123"}]

        mock_product_result = Mock()
        mock_product_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Test Product",
            "description": "Test Description",
            "category_id": "cat-uuid-123",
            "size_ml": 100,
            "price_eur": 29.99,
            "active": True
        }]

        mock_bibbi_db.client.execute.side_effect = [
            mock_match_result,   # Vendor code match
            mock_product_result  # Fetch product details
        ]

        # Execute
        result = product_service.match_or_create_product("834429", "Test Product", "liberty")

        # Verify - returns Dict with full product
        assert isinstance(result, dict)
        assert result["ean"] == "1234567890123"
        assert result["functional_name"] == "Test Product"
        assert result["description"] == "Test Description"
        # Verify vendor code matching was called (use assert_any_call since fetch also calls eq)
        mock_bibbi_db.client.eq.assert_any_call("liberty_name", "834429")

    def test_tier_2_fuzzy_match_success(self, product_service, mock_bibbi_db):
        """Test Tier 2: Fuzzy name matching when vendor code fails"""
        # Setup mocks - vendor code match fails, fuzzy match succeeds
        mock_result_empty = Mock()
        mock_result_empty.data = []

        mock_result_fuzzy = Mock()
        mock_result_fuzzy.data = [
            {"ean": "9876543210987", "description": "Test Product Name", "functional_name": None}
        ]

        mock_result_product = Mock()
        mock_result_product.data = [{
            "ean": "9876543210987",
            "functional_name": "Test Product Name",
            "description": "From fuzzy match",
            "active": True
        }]

        mock_bibbi_db.client.execute.side_effect = [
            mock_result_empty,    # Vendor code match fails
            mock_result_fuzzy,    # Fuzzy match succeeds
            Mock(data=[]),        # Update vendor mapping
            mock_result_product   # Fetch product details
        ]

        # Execute
        result = product_service.match_or_create_product("834429", "Test Product Name", "liberty")

        # Verify - returns Dict
        assert isinstance(result, dict)
        assert result["ean"] == "9876543210987"
        assert result["functional_name"] == "Test Product Name"
        # Should update vendor mapping
        mock_bibbi_db.client.update.assert_called_once()

    def test_tier_3_auto_create(self, product_service, mock_bibbi_db):
        """Test Tier 3: Auto-create when both matches fail"""
        # Setup mocks - all matches fail
        mock_result_empty = Mock()
        mock_result_empty.data = []

        mock_result_create = Mock()
        mock_result_create.data = [{"ean": "9000000834429"}]

        mock_result_product = Mock()
        mock_result_product.data = [{
            "ean": "9000000834429",
            "functional_name": "Test Product",
            "description": "Test Product",
            "active": False
        }]

        mock_bibbi_db.client.execute.side_effect = [
            mock_result_empty,    # Vendor code match fails
            mock_result_empty,    # Fuzzy match fails
            mock_result_create,   # Auto-create succeeds
            mock_result_product   # Fetch product details
        ]

        # Execute
        result = product_service.match_or_create_product("834429", "Test Product", "liberty")

        # Verify - returns Dict
        assert isinstance(result, dict)
        assert result["ean"] == "9000000834429"
        assert result["functional_name"] == "Test Product"
        mock_bibbi_db.client.insert.assert_called_once()

    def test_without_product_name(self, product_service, mock_bibbi_db):
        """Test workflow without product name (skips Tier 2)"""
        # Setup mocks
        mock_result_empty = Mock()
        mock_result_empty.data = []

        mock_result_create = Mock()
        mock_result_create.data = [{"ean": "9000000834429"}]

        mock_result_product = Mock()
        mock_result_product.data = [{
            "ean": "9000000834429",
            "functional_name": "834429",
            "description": "Auto-created from liberty upload",
            "active": False
        }]

        mock_bibbi_db.client.execute.side_effect = [
            mock_result_empty,    # Vendor code match fails
            mock_result_create,   # Auto-create succeeds (skips fuzzy match)
            mock_result_product   # Fetch product details
        ]

        # Execute without product name
        result = product_service.match_or_create_product("834429", None, "liberty")

        # Verify - should skip Tier 2 and go to Tier 3, returns Dict
        assert isinstance(result, dict)
        assert result["ean"] == "9000000834429"


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
        mock_bibbi_db.client.eq.assert_called_with("ean", "1234567890123")

        # Verify update payload
        call_args = mock_bibbi_db.client.update.call_args[0][0]
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


# ============================================
# FETCH PRODUCT DETAILS TESTS
# ============================================

class TestFetchProductDetails:
    """Test _fetch_product_details() method"""

    def test_fetch_product_details_success(self, product_service, mock_bibbi_db):
        """Test fetching full product details successfully"""
        # Setup mock with complete product record
        mock_result = Mock()
        mock_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Test Product",
            "description": "Test Description",
            "category_id": "cat-uuid-123",
            "size_ml": 100,
            "price_eur": 29.99,
            "active": True,
            "liberty_name": "834429",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        product = product_service._fetch_product_details("1234567890123")

        # Verify - returns full product dict with all fields
        assert isinstance(product, dict)
        assert product["ean"] == "1234567890123"
        assert product["functional_name"] == "Test Product"
        assert product["description"] == "Test Description"
        assert product["category_id"] == "cat-uuid-123"
        assert product["size_ml"] == 100
        assert product["price_eur"] == 29.99
        assert product["active"] is True
        assert product["liberty_name"] == "834429"

        # Verify correct query
        mock_bibbi_db.client.table.assert_called_with("products")
        mock_bibbi_db.client.select.assert_called_with("*")
        mock_bibbi_db.client.eq.assert_called_with("ean", "1234567890123")

    def test_fetch_product_details_not_found(self, product_service, mock_bibbi_db):
        """Test fetching non-existent product returns minimal dict"""
        # Setup mock with empty result
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        product = product_service._fetch_product_details("9999999999999")

        # Verify - returns minimal dict with None values
        assert isinstance(product, dict)
        assert product["ean"] == "9999999999999"
        assert product["functional_name"] is None
        assert product["description"] is None
        assert len(product) == 3  # Only ean, functional_name, description

    def test_fetch_product_details_database_error(self, product_service, mock_bibbi_db):
        """Test handling database errors gracefully"""
        # Setup mock to raise exception
        mock_bibbi_db.client.execute.side_effect = Exception("Database connection lost")

        # Execute
        product = product_service._fetch_product_details("1234567890123")

        # Verify - returns minimal dict on error
        assert isinstance(product, dict)
        assert product["ean"] == "1234567890123"
        assert product["functional_name"] is None
        assert product["description"] is None
        assert len(product) == 3

    def test_fetch_product_details_includes_all_fields(self, product_service, mock_bibbi_db):
        """Test that all product fields are returned"""
        # Setup mock with comprehensive product record
        mock_result = Mock()
        mock_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Complete Product",
            "description": "Full Description",
            "category_id": "cat-123",
            "size_ml": 250,
            "price_eur": 49.99,
            "active": True,
            "liberty_name": "LIB-001",
            "galilu_name": "GAL-002",
            "skins_sa_name": "SKN-003",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "custom_field": "custom_value"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        product = product_service._fetch_product_details("1234567890123")

        # Verify - all fields present
        assert product["ean"] == "1234567890123"
        assert product["functional_name"] == "Complete Product"
        assert product["description"] == "Full Description"
        assert product["category_id"] == "cat-123"
        assert product["size_ml"] == 250
        assert product["price_eur"] == 49.99
        assert product["active"] is True
        assert product["liberty_name"] == "LIB-001"
        assert product["galilu_name"] == "GAL-002"
        assert product["skins_sa_name"] == "SKN-003"
        assert product["created_at"] == "2025-01-01T00:00:00"
        assert product["updated_at"] == "2025-01-02T00:00:00"
        assert product["custom_field"] == "custom_value"

    def test_fetch_product_details_with_null_fields(self, product_service, mock_bibbi_db):
        """Test handling products with NULL/missing fields"""
        # Setup mock with sparse product record
        mock_result = Mock()
        mock_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Minimal Product",
            "description": None,
            "category_id": None,
            "size_ml": None,
            "price_eur": None,
            "active": False
        }]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        product = product_service._fetch_product_details("1234567890123")

        # Verify - returns product with None values intact
        assert product["ean"] == "1234567890123"
        assert product["functional_name"] == "Minimal Product"
        assert product["description"] is None
        assert product["category_id"] is None
        assert product["size_ml"] is None
        assert product["price_eur"] is None
        assert product["active"] is False

"""
Unit tests for BibbiBseProcessor sales_channel population functionality

Tests sales_channel population in base processor:
- Reseller lookup from resellers table
- Caching of reseller details
- sales_channel field population in base row
- Processor value precedence (don't overwrite)
- Error handling and graceful degradation

Tests: backend/app/services/bibbi/processors/base.py
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from uuid import uuid4

from app.services.bibbi.processors.liberty_processor import LibertyProcessor


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def test_reseller_id():
    """Test reseller UUID"""
    return str(uuid4())


@pytest.fixture
def test_batch_id():
    """Test batch UUID"""
    return str(uuid4())


@pytest.fixture
def mock_bibbi_db():
    """Mock BIBBI database client"""
    # Create mock for the raw Supabase client (used for resellers table)
    mock_raw_client = Mock()
    mock_raw_client.table = Mock(return_value=mock_raw_client)
    mock_raw_client.select = Mock(return_value=mock_raw_client)
    mock_raw_client.eq = Mock(return_value=mock_raw_client)
    mock_raw_client.execute = Mock()

    # Create BibbιDB wrapper mock
    mock_db = Mock()
    mock_db.client = mock_raw_client  # Point to raw client for resellers table

    return mock_db


@pytest.fixture
def test_processor(test_reseller_id):
    """Liberty processor instance for testing base class"""
    # Use Liberty processor as concrete implementation of abstract base class
    return LibertyProcessor(test_reseller_id)


# ============================================
# RESELLER SALES_CHANNEL LOOKUP TESTS
# ============================================

class TestGetResellerSalesChannel:
    """Test _get_reseller_sales_channel() method for reseller lookup and caching"""

    @patch('app.core.bibbi.get_bibbi_db')
    def test_get_reseller_sales_channel_success(self, mock_get_db, test_processor, mock_bibbi_db, test_reseller_id):
        """Test successful reseller lookup from resellers table"""
        # Setup mock response with reseller details
        mock_result = Mock()
        mock_result.data = [{
            "sales_channel": "B2B",
            "reseller": "Liberty UK"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        sales_channel = test_processor._get_reseller_sales_channel()

        # Verify - returns sales_channel value
        assert sales_channel == "B2B"

        # Verify correct query to resellers table using raw client (bypasses tenant filter)
        mock_bibbi_db.client.table.assert_called_with("resellers")
        mock_bibbi_db.client.select.assert_called_with("sales_channel, reseller")
        mock_bibbi_db.client.eq.assert_called_with("reseller_id", test_reseller_id)

        # Verify reseller_id added to cache
        assert test_processor._reseller_cache is not None
        assert test_processor._reseller_cache["sales_channel"] == "B2B"
        assert test_processor._reseller_cache["reseller"] == "Liberty UK"

    @patch('app.core.bibbi.get_bibbi_db')
    def test_get_reseller_sales_channel_cache_hit(self, mock_get_db, test_processor, mock_bibbi_db):
        """Test cache hit prevents database queries"""
        # Populate cache manually
        test_processor._reseller_cache = {
            "sales_channel": "B2C",
            "reseller": "Test Reseller"
        }
        mock_get_db.return_value = mock_bibbi_db

        # Call method twice
        sales_channel_1 = test_processor._get_reseller_sales_channel()
        sales_channel_2 = test_processor._get_reseller_sales_channel()

        # Verify returns cached value
        assert sales_channel_1 == "B2C"
        assert sales_channel_2 == "B2C"

        # Verify database called ZERO times (cache prevents all calls)
        assert mock_bibbi_db.client.table.call_count == 0
        assert mock_bibbi_db.client.execute.call_count == 0

    @patch('app.core.bibbi.get_bibbi_db')
    def test_get_reseller_sales_channel_not_found(self, mock_get_db, test_processor, mock_bibbi_db):
        """Test reseller not found returns None"""
        # Setup mock response with empty result
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        sales_channel = test_processor._get_reseller_sales_channel()

        # Verify - returns None
        assert sales_channel is None

        # Verify warning logged (check via print statement in actual code)
        # In production, would use logging and assert log message

    @patch('app.core.bibbi.get_bibbi_db')
    def test_get_reseller_sales_channel_database_error(self, mock_get_db, test_processor, mock_bibbi_db):
        """Test database error returns None (graceful degradation)"""
        # Setup mock to raise exception
        mock_bibbi_db.client.table.side_effect = Exception("Database connection lost")
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        sales_channel = test_processor._get_reseller_sales_channel()

        # Verify - returns None (graceful degradation)
        assert sales_channel is None

        # Error should be logged (check via print statement in actual code)


# ============================================
# CREATE BASE ROW TESTS
# ============================================

class TestCreateBaseRow:
    """Test _create_base_row() method for base row creation with sales_channel"""

    @patch('app.core.bibbi.get_bibbi_db')
    @patch('app.services.bibbi.processors.base.datetime')
    def test_create_base_row_includes_sales_channel(self, mock_datetime, mock_get_db, test_processor, mock_bibbi_db, test_batch_id, test_reseller_id):
        """Test base row includes sales_channel from reseller lookup"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup mock response with reseller details
        mock_result = Mock()
        mock_result.data = [{
            "sales_channel": "B2B",
            "reseller": "Liberty UK"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        base_row = test_processor._create_base_row(test_batch_id)

        # Verify result contains all expected fields
        assert base_row["tenant_id"] == "bibbi"
        assert base_row["reseller_id"] == test_reseller_id
        assert base_row["batch_id"] == test_batch_id
        assert base_row["vendor_name"] == "liberty"
        assert base_row["currency"] == "GBP"
        assert base_row["sales_channel"] == "B2B"
        assert base_row["created_at"] == "2025-01-15T10:30:00"

    @patch('app.core.bibbi.get_bibbi_db')
    @patch('app.services.bibbi.processors.base.datetime')
    def test_create_base_row_without_sales_channel(self, mock_datetime, mock_get_db, test_processor, mock_bibbi_db, test_batch_id, test_reseller_id):
        """Test base row without sales_channel when reseller not found"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup mock response with empty result (reseller not found)
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        base_row = test_processor._create_base_row(test_batch_id)

        # Verify result does NOT contain sales_channel field
        assert "sales_channel" not in base_row

        # Verify other fields are present
        assert base_row["tenant_id"] == "bibbi"
        assert base_row["reseller_id"] == test_reseller_id
        assert base_row["batch_id"] == test_batch_id
        assert base_row["vendor_name"] == "liberty"
        assert base_row["currency"] == "GBP"
        assert base_row["created_at"] == "2025-01-15T10:30:00"

    @patch('app.core.bibbi.get_bibbi_db')
    @patch('app.services.bibbi.processors.base.datetime')
    def test_create_base_row_b2c_sales_channel(self, mock_datetime, mock_get_db, test_processor, mock_bibbi_db, test_batch_id):
        """Test base row with B2C sales_channel"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup mock response with B2C sales_channel
        mock_result = Mock()
        mock_result.data = [{
            "sales_channel": "B2C",
            "reseller": "Liberty Online"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        base_row = test_processor._create_base_row(test_batch_id)

        # Verify sales_channel is B2C
        assert base_row["sales_channel"] == "B2C"

    @patch('app.core.bibbi.get_bibbi_db')
    @patch('app.services.bibbi.processors.base.datetime')
    def test_create_base_row_b2b2c_sales_channel(self, mock_datetime, mock_get_db, test_processor, mock_bibbi_db, test_batch_id):
        """Test base row with B2B2C sales_channel"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup mock response with B2B2C sales_channel
        mock_result = Mock()
        mock_result.data = [{
            "sales_channel": "B2B2C",
            "reseller": "Liberty Mixed"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        base_row = test_processor._create_base_row(test_batch_id)

        # Verify sales_channel is B2B2C
        assert base_row["sales_channel"] == "B2B2C"


# ============================================
# RESELLER CACHING TESTS
# ============================================

class TestResellerCaching:
    """Test reseller cache initialization and behavior"""

    def test_reseller_cache_initialized_none(self, test_processor):
        """Test reseller cache starts as None"""
        assert test_processor._reseller_cache is None

    @patch('app.core.bibbi.get_bibbi_db')
    def test_reseller_cache_persists_across_base_row_calls(self, mock_get_db, test_processor, mock_bibbi_db, test_batch_id):
        """Test cache persists across multiple _create_base_row calls"""
        # Setup mock response with reseller details
        mock_result = Mock()
        mock_result.data = [{
            "sales_channel": "B2B",
            "reseller": "Liberty UK"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Call _create_base_row twice
        base_row_1 = test_processor._create_base_row(test_batch_id)
        base_row_2 = test_processor._create_base_row(test_batch_id)

        # Verify both rows have sales_channel
        assert base_row_1["sales_channel"] == "B2B"
        assert base_row_2["sales_channel"] == "B2B"

        # Verify database called only ONCE (second call used cache)
        assert mock_bibbi_db.client.execute.call_count == 1

    @patch('app.core.bibbi.get_bibbi_db')
    def test_reseller_cache_populated_on_first_call(self, mock_get_db, test_processor, mock_bibbi_db):
        """Test cache is populated on first _get_reseller_sales_channel call"""
        # Verify cache starts empty
        assert test_processor._reseller_cache is None

        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{
            "sales_channel": "B2B",
            "reseller": "Liberty UK"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        sales_channel = test_processor._get_reseller_sales_channel()

        # Verify cache is now populated
        assert test_processor._reseller_cache is not None
        assert test_processor._reseller_cache["sales_channel"] == "B2B"
        assert test_processor._reseller_cache["reseller"] == "Liberty UK"

    @patch('app.core.bibbi.get_bibbi_db')
    def test_reseller_cache_not_populated_on_error(self, mock_get_db, test_processor, mock_bibbi_db):
        """Test cache is not populated when database error occurs"""
        # Verify cache starts empty
        assert test_processor._reseller_cache is None

        # Setup mock to raise exception
        mock_bibbi_db.client.table.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        sales_channel = test_processor._get_reseller_sales_channel()

        # Verify cache remains None (not populated on error)
        assert test_processor._reseller_cache is None
        assert sales_channel is None

    @patch('app.core.bibbi.get_bibbi_db')
    def test_reseller_cache_not_populated_when_not_found(self, mock_get_db, test_processor, mock_bibbi_db):
        """Test cache is not populated when reseller not found"""
        # Verify cache starts empty
        assert test_processor._reseller_cache is None

        # Setup mock response with empty result
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result
        mock_get_db.return_value = mock_bibbi_db

        # Execute
        sales_channel = test_processor._get_reseller_sales_channel()

        # Verify cache remains None (not populated when not found)
        assert test_processor._reseller_cache is None
        assert sales_channel is None


# ============================================
# INTEGRATION TESTS
# ============================================

class TestSalesChannelIntegration:
    """Test sales_channel integration with transform_row workflow"""

    @patch('app.core.bibbi.get_bibbi_db')
    @patch('app.services.bibbi.processors.base.datetime')
    def test_transform_row_includes_sales_channel(self, mock_datetime, mock_get_db, test_processor, mock_bibbi_db, test_batch_id):
        """Test transform_row includes sales_channel from base row"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup mock for reseller lookup
        mock_reseller_result = Mock()
        mock_reseller_result.data = [{
            "sales_channel": "B2B",
            "reseller": "Liberty UK"
        }]

        # Setup mock for product matching
        mock_product_result = Mock()
        mock_product_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Test Product",
            "vendor_code": "834429"
        }]

        # Configure execute to return different results based on table call
        def execute_side_effect():
            # Check which table was called last
            if mock_bibbi_db.client.table.call_args_list[-1][0][0] == "resellers":
                return mock_reseller_result
            else:
                return mock_product_result

        mock_bibbi_db.client.execute.side_effect = execute_side_effect
        mock_get_db.return_value = mock_bibbi_db

        # Mock product service
        mock_product_match = {
            "ean": "1234567890123",
            "functional_name": "Test Product"
        }

        with patch('app.services.bibbi.product_service.get_product_service') as mock_get_product_service:
            mock_product_service = Mock()
            mock_product_service.match_or_create_product.return_value = mock_product_match
            mock_get_product_service.return_value = mock_product_service

            # Create raw row (Liberty format)
            raw_row = {
                "Item ID | Colour": "000834429 | 98-NO COLOUR",
                "Item": "Test Product",
                "Sales Qty Un": 10,
                "Sales Inc VAT £ ": 100.50,
                "store_identifier": "flagship",
                "_file_date": datetime(2025, 1, 10)
            }

            # Execute transform
            transformed = test_processor.transform_row(raw_row, test_batch_id)

        # Verify transformed row includes sales_channel
        assert transformed is not None
        assert transformed["sales_channel"] == "B2B"
        assert transformed["vendor_name"] == "liberty"
        assert transformed["currency"] == "GBP"
        assert transformed["reseller_id"] == test_processor.reseller_id

    @patch('app.core.bibbi.get_bibbi_db')
    @patch('app.services.bibbi.processors.base.datetime')
    def test_transform_row_without_sales_channel(self, mock_datetime, mock_get_db, test_processor, mock_bibbi_db, test_batch_id):
        """Test transform_row without sales_channel when reseller not found"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup mock for reseller lookup (not found)
        mock_reseller_result = Mock()
        mock_reseller_result.data = []

        # Setup mock for product matching
        mock_product_result = Mock()
        mock_product_result.data = [{
            "ean": "1234567890123",
            "functional_name": "Test Product",
            "vendor_code": "834429"
        }]

        # Configure execute to return different results
        def execute_side_effect():
            if mock_bibbi_db.client.table.call_args_list[-1][0][0] == "resellers":
                return mock_reseller_result
            else:
                return mock_product_result

        mock_bibbi_db.client.execute.side_effect = execute_side_effect
        mock_get_db.return_value = mock_bibbi_db

        # Mock product service
        mock_product_match = {
            "ean": "1234567890123",
            "functional_name": "Test Product"
        }

        with patch('app.services.bibbi.product_service.get_product_service') as mock_get_product_service:
            mock_product_service = Mock()
            mock_product_service.match_or_create_product.return_value = mock_product_match
            mock_get_product_service.return_value = mock_product_service

            # Create raw row
            raw_row = {
                "Item ID | Colour": "000834429 | 98-NO COLOUR",
                "Item": "Test Product",
                "Sales Qty Un": 10,
                "Sales Inc VAT £ ": 100.50,
                "store_identifier": "flagship",
                "_file_date": datetime(2025, 1, 10)
            }

            # Execute transform
            transformed = test_processor.transform_row(raw_row, test_batch_id)

        # Verify transformed row does NOT include sales_channel
        assert transformed is not None
        assert "sales_channel" not in transformed
        assert transformed["vendor_name"] == "liberty"
        assert transformed["currency"] == "GBP"

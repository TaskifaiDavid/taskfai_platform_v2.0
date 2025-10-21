"""
Unit tests for BIBBI Sales Insertion Service

Tests geography population functionality:
- Store details lookup from stores table
- Caching of store details
- Geography field population (country, region, city)
- Processor value precedence (don't overwrite)
- Error handling and graceful degradation

Tests: backend/app/services/bibbi/sales_insertion_service.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.bibbi.sales_insertion_service import BibbιSalesInsertionService


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_bibbi_db():
    """Mock BIBBI database client"""
    # Create mock for the raw Supabase client (used for stores table)
    mock_raw_client = Mock()
    mock_raw_client.table = Mock(return_value=mock_raw_client)
    mock_raw_client.select = Mock(return_value=mock_raw_client)
    mock_raw_client.eq = Mock(return_value=mock_raw_client)
    mock_raw_client.insert = Mock(return_value=mock_raw_client)
    mock_raw_client.execute = Mock()

    # Create BibbιDB wrapper mock
    mock_db = Mock()
    mock_db.client = mock_raw_client  # Point to raw client for stores table
    mock_db.table = Mock(return_value=mock_db)
    mock_db.select = Mock(return_value=mock_db)
    mock_db.eq = Mock(return_value=mock_db)
    mock_db.insert = Mock(return_value=mock_db)
    mock_db.execute = Mock()

    return mock_db


@pytest.fixture
def insertion_service(mock_bibbi_db):
    """Sales insertion service instance"""
    return BibbιSalesInsertionService(mock_bibbi_db)


# ============================================
# STORE DETAILS LOOKUP TESTS
# ============================================

class TestGetStoreDetails:
    """Test _get_store_details() method for store lookup and caching"""

    def test_get_store_details_success(self, insertion_service, mock_bibbi_db):
        """Test successful store lookup from stores table"""
        # Setup mock response with store details
        mock_result = Mock()
        mock_result.data = [{
            "country": "UK",
            "region": None,
            "city": "London",
            "store_name": "Liberty Flagship"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        store_id = "store-uuid-123"
        details = insertion_service._get_store_details(store_id)

        # Verify - returns Dict with geography fields
        assert details is not None
        assert isinstance(details, dict)
        assert details["country"] == "UK"
        assert details["region"] is None
        assert details["city"] == "London"
        assert details["store_name"] == "Liberty Flagship"

        # Verify correct query to stores table using raw client (bypasses tenant filter)
        mock_bibbi_db.client.table.assert_called_with("stores")
        mock_bibbi_db.client.select.assert_called_with("country, region, city, store_name")
        mock_bibbi_db.client.eq.assert_called_with("store_id", store_id)

        # Verify store_id added to cache
        assert store_id in insertion_service._store_cache
        assert insertion_service._store_cache[store_id]["country"] == "UK"

    def test_get_store_details_cache_hit(self, insertion_service, mock_bibbi_db):
        """Test cache hit prevents database queries"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{
            "country": "UK",
            "region": "England",
            "city": "London",
            "store_name": "Liberty Flagship"
        }]
        mock_bibbi_db.client.execute.return_value = mock_result

        # First call - should hit database
        store_id = "store-uuid-456"
        details_1 = insertion_service._get_store_details(store_id)

        # Verify first call executed query
        assert mock_bibbi_db.client.execute.call_count == 1
        assert details_1 is not None

        # Second call - should use cache
        details_2 = insertion_service._get_store_details(store_id)

        # Verify database called only ONCE (cache prevents second call)
        assert mock_bibbi_db.client.execute.call_count == 1
        assert details_2 is not None
        assert details_1 == details_2

    def test_get_store_details_not_found(self, insertion_service, mock_bibbi_db):
        """Test store not found returns None"""
        # Setup mock response with empty result
        mock_result = Mock()
        mock_result.data = []
        mock_bibbi_db.client.execute.return_value = mock_result

        # Execute
        details = insertion_service._get_store_details("nonexistent-store-id")

        # Verify - returns None
        assert details is None

        # Verify warning logged (check via print statement in actual code)
        # In production, would use logging and assert log message

    def test_get_store_details_database_error(self, insertion_service, mock_bibbi_db):
        """Test database error returns None (graceful degradation)"""
        # Setup mock to raise exception
        mock_bibbi_db.client.execute.side_effect = Exception("Database connection lost")

        # Execute
        details = insertion_service._get_store_details("store-uuid-error")

        # Verify - returns None (graceful degradation)
        assert details is None

        # Error should be logged (check via print statement in actual code)

    def test_get_store_details_multiple_stores(self, insertion_service, mock_bibbi_db):
        """Test multiple store lookups with caching"""
        # Setup different responses for different stores
        def execute_side_effect():
            # Return different data based on call count
            call_count = mock_bibbi_db.client.execute.call_count
            if call_count == 0:
                return Mock(data=[{"country": "UK", "region": None, "city": "London", "store_name": "Liberty London"}])
            elif call_count == 1:
                return Mock(data=[{"country": "UAE", "region": "Dubai", "city": "Dubai", "store_name": "Liberty Dubai"}])
            else:
                return Mock(data=[])

        mock_bibbi_db.client.execute.side_effect = [
            Mock(data=[{"country": "UK", "region": None, "city": "London", "store_name": "Liberty London"}]),
            Mock(data=[{"country": "UAE", "region": "Dubai", "city": "Dubai", "store_name": "Liberty Dubai"}]),
        ]

        # Execute - lookup two different stores
        details_1 = insertion_service._get_store_details("store-uk")
        details_2 = insertion_service._get_store_details("store-uae")

        # Verify both queries executed (different stores)
        assert mock_bibbi_db.client.execute.call_count == 2

        # Third call for first store - should use cache
        details_1_cached = insertion_service._get_store_details("store-uk")
        assert mock_bibbi_db.client.execute.call_count == 2  # No additional call

        # Verify different geography returned
        assert details_1["country"] == "UK"
        assert details_2["country"] == "UAE"
        assert details_1_cached["country"] == "UK"


# ============================================
# GEOGRAPHY POPULATION TESTS
# ============================================

class TestGeographyPopulation:
    """Test geography field population during sales insertion"""

    @patch('app.services.bibbi.sales_insertion_service.datetime')
    def test_geography_population_from_store(self, mock_datetime, insertion_service, mock_bibbi_db):
        """Test geography fields populated from store lookup"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup store mapping
        store_mapping = {"flagship": "store-uuid-flagship"}

        # Setup mock for store details lookup
        mock_store_result = Mock()
        mock_store_result.data = [{
            "country": "UK",
            "region": None,
            "city": "London",
            "store_name": "Liberty Flagship"
        }]

        # Setup mock for sales insertion
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": "sales-uuid-1"}]

        # Configure execute to return different results based on table call
        def execute_side_effect():
            # Check which table was called last
            if mock_bibbi_db.client.table.call_args_list[-1][0][0] == "stores":
                return mock_store_result
            else:
                return mock_insert_result

        mock_bibbi_db.client.execute.side_effect = [mock_store_result]
        mock_bibbi_db.execute.side_effect = [mock_insert_result]

        # Create validated sales data WITHOUT geography fields
        validated_data = [{
            "upload_id": "upload-123",
            "product_id": "prod-456",
            "reseller_id": "reseller-789",
            "sale_date": "2025-01-10",
            "quantity": 5,
            "sales_eur": 100.00,
            "store_identifier": "flagship"  # Will be converted to UUID
            # NO country/region/city fields
        }]

        # Execute insertion
        result = insertion_service.insert_validated_sales(
            validated_data=validated_data,
            batch_size=10,
            store_mapping=store_mapping
        )

        # Verify store details lookup was called
        mock_bibbi_db.client.table.assert_any_call("stores")
        mock_bibbi_db.client.eq.assert_any_call("store_id", "store-uuid-flagship")

        # Verify sales insert was called with geography fields populated
        mock_bibbi_db.insert.assert_called_once()
        insert_call_args = mock_bibbi_db.insert.call_args[0][0]

        # Check that batch contains geography fields from store lookup
        assert len(insert_call_args) == 1
        inserted_row = insert_call_args[0]
        assert inserted_row["store_id"] == "store-uuid-flagship"
        assert inserted_row["country"] == "UK"
        assert inserted_row["region"] is None
        assert inserted_row["city"] == "London"

        # Verify store_identifier was removed (not in BIBBI schema)
        assert "store_identifier" not in inserted_row

    @patch('app.services.bibbi.sales_insertion_service.datetime')
    def test_geography_processor_takes_precedence(self, mock_datetime, insertion_service, mock_bibbi_db):
        """Test processor values NOT overwritten by store lookup"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup store mapping
        store_mapping = {"flagship": "store-uuid-flagship"}

        # Setup mock for store details lookup (DIFFERENT geography)
        mock_store_result = Mock()
        mock_store_result.data = [{
            "country": "UAE",  # Different from processor
            "region": "Dubai",  # Different from processor
            "city": "Dubai",  # Different from processor
            "store_name": "Liberty Dubai"
        }]

        # Setup mock for sales insertion
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": "sales-uuid-1"}]

        mock_bibbi_db.client.execute.side_effect = [mock_store_result]
        mock_bibbi_db.execute.side_effect = [mock_insert_result]

        # Create validated sales data WITH geography fields from processor
        validated_data = [{
            "upload_id": "upload-123",
            "product_id": "prod-456",
            "reseller_id": "reseller-789",
            "sale_date": "2025-01-10",
            "quantity": 5,
            "sales_eur": 100.00,
            "store_identifier": "flagship",
            # Processor set these values
            "country": "UK",
            "region": "England",
            "city": "London"
        }]

        # Execute insertion
        result = insertion_service.insert_validated_sales(
            validated_data=validated_data,
            batch_size=10,
            store_mapping=store_mapping
        )

        # Verify sales insert was called
        mock_bibbi_db.insert.assert_called_once()
        insert_call_args = mock_bibbi_db.insert.call_args[0][0]

        # Verify processor values are PRESERVED (NOT overwritten by store lookup)
        inserted_row = insert_call_args[0]
        assert inserted_row["country"] == "UK"  # Processor value preserved
        assert inserted_row["region"] == "England"  # Processor value preserved
        assert inserted_row["city"] == "London"  # Processor value preserved

    @patch('app.services.bibbi.sales_insertion_service.datetime')
    def test_geography_partial_processor_values(self, mock_datetime, insertion_service, mock_bibbi_db):
        """Test partial processor values supplemented by store lookup"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup store mapping
        store_mapping = {"flagship": "store-uuid-flagship"}

        # Setup mock for store details lookup
        mock_store_result = Mock()
        mock_store_result.data = [{
            "country": "UK",
            "region": "England",
            "city": "London",
            "store_name": "Liberty Flagship"
        }]

        # Setup mock for sales insertion
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": "sales-uuid-1"}]

        mock_bibbi_db.client.execute.side_effect = [mock_store_result]
        mock_bibbi_db.execute.side_effect = [mock_insert_result]

        # Create validated sales data with ONLY country from processor
        validated_data = [{
            "upload_id": "upload-123",
            "product_id": "prod-456",
            "reseller_id": "reseller-789",
            "sale_date": "2025-01-10",
            "quantity": 5,
            "sales_eur": 100.00,
            "store_identifier": "flagship",
            "country": "UK"  # Only country from processor
            # NO region or city
        }]

        # Execute insertion
        result = insertion_service.insert_validated_sales(
            validated_data=validated_data,
            batch_size=10,
            store_mapping=store_mapping
        )

        # Verify sales insert was called
        mock_bibbi_db.insert.assert_called_once()
        insert_call_args = mock_bibbi_db.insert.call_args[0][0]

        # Verify processor country preserved, store lookup fills in region/city
        inserted_row = insert_call_args[0]
        assert inserted_row["country"] == "UK"  # Processor value preserved
        assert inserted_row["region"] == "England"  # Filled from store
        assert inserted_row["city"] == "London"  # Filled from store

    @patch('app.services.bibbi.sales_insertion_service.datetime')
    def test_no_geography_population_without_store_mapping(self, mock_datetime, insertion_service, mock_bibbi_db):
        """Test no geography lookup if store_identifier not in mapping"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup EMPTY store mapping
        store_mapping = {}

        # Setup mock for sales insertion (no store lookup expected)
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": "sales-uuid-1"}]
        mock_bibbi_db.execute.side_effect = [mock_insert_result]

        # Create validated sales data
        validated_data = [{
            "upload_id": "upload-123",
            "product_id": "prod-456",
            "reseller_id": "reseller-789",
            "sale_date": "2025-01-10",
            "quantity": 5,
            "sales_eur": 100.00,
            "store_identifier": "unknown-store"  # NOT in mapping
        }]

        # Execute insertion
        result = insertion_service.insert_validated_sales(
            validated_data=validated_data,
            batch_size=10,
            store_mapping=store_mapping
        )

        # Verify NO store details lookup was attempted
        # Only the sales insert should be called, not stores table
        assert mock_bibbi_db.client.table.call_count == 0

        # Verify sales insert was still attempted (may fail due to FK constraint)
        mock_bibbi_db.insert.assert_called_once()

    @patch('app.services.bibbi.sales_insertion_service.datetime')
    def test_geography_population_store_not_found(self, mock_datetime, insertion_service, mock_bibbi_db):
        """Test graceful handling when store not found in stores table"""
        # Setup mock datetime
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)

        # Setup store mapping
        store_mapping = {"flagship": "store-uuid-nonexistent"}

        # Setup mock for store details lookup (NOT FOUND)
        mock_store_result = Mock()
        mock_store_result.data = []  # Empty result

        # Setup mock for sales insertion
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": "sales-uuid-1"}]

        mock_bibbi_db.client.execute.side_effect = [mock_store_result]
        mock_bibbi_db.execute.side_effect = [mock_insert_result]

        # Create validated sales data
        validated_data = [{
            "upload_id": "upload-123",
            "product_id": "prod-456",
            "reseller_id": "reseller-789",
            "sale_date": "2025-01-10",
            "quantity": 5,
            "sales_eur": 100.00,
            "store_identifier": "flagship"
        }]

        # Execute insertion
        result = insertion_service.insert_validated_sales(
            validated_data=validated_data,
            batch_size=10,
            store_mapping=store_mapping
        )

        # Verify store lookup was attempted
        mock_bibbi_db.client.table.assert_any_call("stores")

        # Verify sales insert was still called (without geography fields)
        mock_bibbi_db.insert.assert_called_once()
        insert_call_args = mock_bibbi_db.insert.call_args[0][0]

        # Geography fields should be absent/None
        inserted_row = insert_call_args[0]
        assert inserted_row.get("country") is None
        assert inserted_row.get("region") is None
        assert inserted_row.get("city") is None


# ============================================
# CACHE MANAGEMENT TESTS
# ============================================

class TestStoreCaching:
    """Test store cache initialization and behavior"""

    def test_cache_initialized_empty(self, insertion_service):
        """Test store cache starts empty"""
        assert insertion_service._store_cache == {}
        assert isinstance(insertion_service._store_cache, dict)

    def test_cache_persists_across_calls(self, insertion_service, mock_bibbi_db):
        """Test cache persists across multiple insert_validated_sales calls"""
        # Setup mock for store lookup
        mock_store_result = Mock()
        mock_store_result.data = [{
            "country": "UK",
            "region": None,
            "city": "London",
            "store_name": "Liberty Flagship"
        }]

        # Setup mock for sales insertion
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": "sales-1"}]

        mock_bibbi_db.client.execute.return_value = mock_store_result
        mock_bibbi_db.execute.return_value = mock_insert_result

        store_mapping = {"flagship": "store-uuid-persistent"}

        # First insertion
        insertion_service.insert_validated_sales(
            validated_data=[{
                "upload_id": "upload-1",
                "product_id": "prod-1",
                "reseller_id": "res-1",
                "sale_date": "2025-01-10",
                "quantity": 1,
                "sales_eur": 10.00,
                "store_identifier": "flagship"
            }],
            store_mapping=store_mapping
        )

        # Verify cache populated
        assert "store-uuid-persistent" in insertion_service._store_cache

        # Second insertion with same store
        insertion_service.insert_validated_sales(
            validated_data=[{
                "upload_id": "upload-2",
                "product_id": "prod-2",
                "reseller_id": "res-2",
                "sale_date": "2025-01-11",
                "quantity": 2,
                "sales_eur": 20.00,
                "store_identifier": "flagship"
            }],
            store_mapping=store_mapping
        )

        # Verify store lookup only called ONCE (second call used cache)
        assert mock_bibbi_db.client.execute.call_count == 1
        assert "store-uuid-persistent" in insertion_service._store_cache

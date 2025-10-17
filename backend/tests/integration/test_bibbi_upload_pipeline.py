"""
Integration tests for BIBBI upload pipeline

Tests end-to-end flow from file upload to sales insertion.

Pipeline: Upload API → Celery Task → Staging → Detection →
          Routing → Processing → Validation → Insertion
"""

import pytest
import tempfile
import openpyxl
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.bibbi.staging_service import BibbιStagingService
from app.services.bibbi.vendor_detector import detect_bibbi_vendor
from app.services.bibbi.vendor_router import route_bibbi_vendor
from app.services.bibbi.validation_service import BibbιValidationService
from app.services.bibbi.sales_insertion_service import BibbιSalesInsertionService


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_bibbi_db():
    """Mock BIBBI database client"""
    mock_db = Mock()
    mock_client = Mock()
    mock_table = Mock()

    # Mock table operations
    mock_execute = Mock()
    mock_execute.data = []
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = mock_execute

    mock_client.table.return_value = mock_table
    mock_db.client = mock_client
    mock_db.table = mock_client.table

    return mock_db


@pytest.fixture
def test_reseller_id():
    """Test reseller UUID"""
    return "3eae3da5-f2af-449c-8000-d4874c955a05"


@pytest.fixture
def test_batch_id():
    """Test batch UUID"""
    return "4fbf4ea6-g3bg-550d-9111-e5985da066b16"


@pytest.fixture
def sample_boxnox_file():
    """Create sample Boxnox Excel file"""
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sell Out by EAN"

    # Headers
    ws.append(["Product EAN", "Functional Name", "Sold Qty", "Sales Amount (EUR)", "Month", "Year"])

    # Data rows
    ws.append(["1234567890123", "Product A", 10, 100.50, "January", 2024])
    ws.append(["9876543210987", "Product B", 5, 50.25, "February", 2024])

    wb.save(tmp.name)
    wb.close()

    return tmp.name


# ============================================
# STAGING SERVICE TESTS
# ============================================

class TestStagingService:
    """Test staging service"""

    def test_stage_upload_creates_record(self, mock_bibbi_db, test_batch_id, sample_boxnox_file):
        """Test that staging creates a database record"""
        staging_service = BibbιStagingService(mock_bibbi_db)

        # Mock insert response
        mock_execute = Mock()
        mock_execute.data = [{"staging_id": "test-staging-id"}]
        mock_bibbi_db.client.table().insert().execute.return_value = mock_execute

        staging_id = staging_service.stage_upload(test_batch_id, sample_boxnox_file)

        assert staging_id is not None
        mock_bibbi_db.client.table.assert_called_with("bibbi_staging")

        Path(sample_boxnox_file).unlink()

    def test_staging_extracts_file_metadata(self, mock_bibbi_db, test_batch_id, sample_boxnox_file):
        """Test that staging extracts file metadata"""
        staging_service = BibbιStagingService(mock_bibbi_db)

        # Mock insert response
        mock_execute = Mock()
        mock_execute.data = [{"staging_id": "test-staging-id"}]
        mock_bibbi_db.client.table().insert().execute.return_value = mock_execute

        staging_id = staging_service.stage_upload(test_batch_id, sample_boxnox_file)

        # Verify that insert was called (metadata was extracted)
        mock_bibbi_db.client.table().insert.assert_called_once()

        Path(sample_boxnox_file).unlink()


# ============================================
# VENDOR DETECTION TESTS
# ============================================

class TestVendorDetection:
    """Test vendor detection in pipeline"""

    def test_detects_boxnox_from_file(self, sample_boxnox_file):
        """Test detection of Boxnox vendor"""
        vendor_name, confidence, metadata = detect_bibbi_vendor(sample_boxnox_file)

        assert vendor_name == "boxnox"
        assert confidence >= 0.5
        assert isinstance(metadata, dict)

        Path(sample_boxnox_file).unlink()

    def test_high_confidence_for_clear_patterns(self, sample_boxnox_file):
        """Test high confidence for files with clear vendor patterns"""
        vendor_name, confidence, metadata = detect_bibbi_vendor(sample_boxnox_file)

        # Should have high confidence for clear Boxnox patterns
        assert confidence >= 0.6

        Path(sample_boxnox_file).unlink()


# ============================================
# ROUTING TESTS
# ============================================

class TestVendorRouting:
    """Test vendor routing"""

    def test_routes_to_correct_processor(self, mock_bibbi_db, test_reseller_id):
        """Test routing to appropriate processor"""
        processor = route_bibbi_vendor("boxnox", test_reseller_id, mock_bibbi_db)

        assert processor is not None
        assert hasattr(processor, "process")

    def test_routes_all_known_vendors(self, mock_bibbi_db, test_reseller_id):
        """Test routing for all known vendors"""
        vendors = [
            "boxnox", "galilu", "skins_sa", "cdlc",
            "liberty", "selfridges", "skins_nl", "aromateque"
        ]

        for vendor in vendors:
            processor = route_bibbi_vendor(vendor, test_reseller_id, mock_bibbi_db)
            assert processor is not None


# ============================================
# VALIDATION SERVICE TESTS
# ============================================

class TestValidationService:
    """Test validation service in pipeline"""

    def test_validates_correct_data(self, mock_bibbi_db, test_reseller_id):
        """Test validation of correctly formatted data"""
        validation_service = BibbιValidationService(mock_bibbi_db)

        # Valid transformed data
        transformed_data = [{
            "product_id": "1234567890123",
            "reseller_id": test_reseller_id,
            "sale_date": "2024-01-15",
            "quantity": 10,
            "sales_eur": 100.50,
            "tenant_id": "bibbi",
            "year": 2024,
            "month": 1,
            "quarter": 1
        }]

        result = validation_service.validate_transformed_data(transformed_data)

        assert result.total_rows == 1
        assert result.valid_rows == 1
        assert result.invalid_rows == 0

    def test_rejects_invalid_tenant_id(self, mock_bibbi_db, test_reseller_id):
        """Test rejection of non-bibbi tenant data"""
        validation_service = BibbιValidationService(mock_bibbi_db)

        # Invalid tenant_id
        transformed_data = [{
            "product_id": "1234567890123",
            "reseller_id": test_reseller_id,
            "sale_date": "2024-01-15",
            "quantity": 10,
            "sales_eur": 100.50,
            "tenant_id": "demo",  # WRONG! Should be "bibbi"
            "year": 2024,
            "month": 1,
            "quarter": 1
        }]

        result = validation_service.validate_transformed_data(transformed_data)

        # Should fail validation due to wrong tenant_id
        assert result.invalid_rows > 0

    def test_rejects_missing_required_fields(self, mock_bibbi_db, test_reseller_id):
        """Test rejection of data missing required fields"""
        validation_service = BibbιValidationService(mock_bibbi_db)

        # Missing required field (quantity)
        transformed_data = [{
            "product_id": "1234567890123",
            "reseller_id": test_reseller_id,
            "sale_date": "2024-01-15",
            # Missing: quantity
            "sales_eur": 100.50,
            "tenant_id": "bibbi",
            "year": 2024,
            "month": 1,
            "quarter": 1
        }]

        result = validation_service.validate_transformed_data(transformed_data)

        assert result.invalid_rows == 1


# ============================================
# END-TO-END PIPELINE TESTS
# ============================================

class TestEndToEndPipeline:
    """Test complete upload pipeline"""

    def test_pipeline_processes_file_successfully(self, mock_bibbi_db, test_reseller_id, test_batch_id, sample_boxnox_file):
        """Test complete pipeline from detection to validation"""

        # Step 1: Vendor Detection
        vendor_name, confidence, metadata = detect_bibbi_vendor(sample_boxnox_file)
        assert vendor_name == "boxnox"

        # Step 2: Routing
        processor = route_bibbi_vendor(vendor_name, test_reseller_id, mock_bibbi_db)
        assert processor is not None

        # Step 3: Processing
        processing_result = processor.process(sample_boxnox_file, test_batch_id)
        assert processing_result.total_rows > 0
        assert processing_result.successful_rows > 0

        # Step 4: Validation
        validation_service = BibbιValidationService(mock_bibbi_db)
        validation_result = validation_service.validate_transformed_data(
            processing_result.transformed_data
        )
        assert validation_result.valid_rows > 0

        Path(sample_boxnox_file).unlink()

    def test_pipeline_handles_invalid_data(self, mock_bibbi_db, test_reseller_id):
        """Test pipeline handling of invalid data"""

        # Invalid transformed data (negative quantity)
        invalid_data = [{
            "product_id": "1234567890123",
            "reseller_id": test_reseller_id,
            "sale_date": "2024-01-15",
            "quantity": -10,  # Invalid: negative
            "sales_eur": 100.50,
            "tenant_id": "bibbi",
            "year": 2024,
            "month": 1,
            "quarter": 1
        }]

        validation_service = BibbιValidationService(mock_bibbi_db)
        result = validation_service.validate_transformed_data(invalid_data)

        # Should catch invalid quantity
        assert result.invalid_rows > 0


# ============================================
# ERROR RECOVERY TESTS
# ============================================

class TestErrorRecovery:
    """Test error recovery in pipeline"""

    def test_recovers_from_processing_errors(self, mock_bibbi_db, test_reseller_id, test_batch_id):
        """Test recovery from processing errors"""

        # Create corrupted file
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(b"Not a valid Excel file")
            tmp.flush()

            # Should handle error gracefully in detection
            vendor_name, confidence, metadata = detect_bibbi_vendor(tmp.name)

            # Should return None or low confidence for corrupted files
            assert vendor_name is None or confidence < 0.5

            Path(tmp.name).unlink()

    def test_continues_after_partial_failures(self, mock_bibbi_db, test_reseller_id, test_batch_id):
        """Test that pipeline continues processing after partial failures"""

        # Mixed valid and invalid data
        mixed_data = [
            {
                "product_id": "1234567890123",
                "reseller_id": test_reseller_id,
                "sale_date": "2024-01-15",
                "quantity": 10,
                "sales_eur": 100.50,
                "tenant_id": "bibbi",
                "year": 2024,
                "month": 1,
                "quarter": 1
            },
            {
                "product_id": "invalid",  # Invalid EAN
                "reseller_id": test_reseller_id,
                "sale_date": "2024-01-15",
                "quantity": 10,
                "sales_eur": 100.50,
                "tenant_id": "bibbi",
                "year": 2024,
                "month": 1,
                "quarter": 1
            },
            {
                "product_id": "9876543210987",
                "reseller_id": test_reseller_id,
                "sale_date": "2024-01-15",
                "quantity": 5,
                "sales_eur": 50.25,
                "tenant_id": "bibbi",
                "year": 2024,
                "month": 1,
                "quarter": 1
            }
        ]

        validation_service = BibbιValidationService(mock_bibbi_db)
        result = validation_service.validate_transformed_data(mixed_data)

        # Should have both valid and invalid rows
        assert result.valid_rows > 0
        assert result.invalid_rows > 0
        assert result.total_rows == 3


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestPipelinePerformance:
    """Test pipeline performance characteristics"""

    def test_processes_large_file_efficiently(self, mock_bibbi_db, test_reseller_id, test_batch_id):
        """Test processing of large files"""

        # Create file with many rows
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sell Out by EAN"

            ws.append(["Product EAN", "Functional Name", "Sold Qty", "Sales Amount (EUR)", "Month", "Year"])

            # Add 100 rows
            for i in range(100):
                ws.append([f"123456789012{i % 10}", f"Product {i}", 10, 100.50, "January", 2024])

            wb.save(tmp.name)
            wb.close()

            # Should process without timeout
            processor = route_bibbi_vendor("boxnox", test_reseller_id, mock_bibbi_db)
            result = processor.process(tmp.name, test_batch_id)

            assert result.total_rows == 100

            Path(tmp.name).unlink()

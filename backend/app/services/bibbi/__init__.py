"""
BIBBI Services Package

Services for BIBBI tenant-isolated reseller data processing.

Modules:
- staging_service: Raw file staging and metadata extraction
- vendor_detector: Automatic vendor detection from files
- vendor_router: Vendor → processor routing
- validation_service: Row-level data validation
- error_report_service: Excel validation error report generation
- store_service: Store auto-creation and mapping
- product_mapping_service: Product code → EAN mapping
- sales_insertion_service: Final data insertion to sales_unified
"""

from .staging_service import BibbιStagingService, get_staging_service
from .vendor_detector import BibbιVendorDetector, detect_bibbi_vendor
from .vendor_router import BibbιVendorRouter, route_bibbi_vendor
from .validation_service import BibbιValidationService, ValidationResult, get_validation_service
from .error_report_service import BibbιErrorReportService, get_error_report_service
from .store_service import BibbιStoreService, get_store_service
from .product_mapping_service import BibbιProductMappingService, get_product_mapping_service
from .sales_insertion_service import BibbιSalesInsertionService, InsertionResult, get_sales_insertion_service

__all__ = [
    "BibbιStagingService",
    "get_staging_service",
    "BibbιVendorDetector",
    "detect_bibbi_vendor",
    "BibbιVendorRouter",
    "route_bibbi_vendor",
    "BibbιValidationService",
    "ValidationResult",
    "get_validation_service",
    "BibbιErrorReportService",
    "get_error_report_service",
    "BibbιStoreService",
    "get_store_service",
    "BibbιProductMappingService",
    "get_product_mapping_service",
    "BibbιSalesInsertionService",
    "InsertionResult",
    "get_sales_insertion_service",
]

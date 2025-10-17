"""
BIBBI Vendor Router Service

Routes detected vendors to their appropriate processor classes.

Maps vendor names → processor instances with BIBBI tenant context.
"""

from typing import Optional, Dict, Any

from .vendor_detector import detect_bibbi_vendor


class BibbιVendorRouter:
    """
    Routes BIBBI vendors to their processors

    Workflow:
    1. Detect vendor from file (via vendor_detector)
    2. Map vendor → processor class
    3. Return processor instance with tenant context

    Supported processors:
    - aromateque_processor
    - boxnox_processor
    - cdlc_processor (Creme de la Creme)
    - galilu_processor
    - liberty_processor
    - selfridges_processor
    - skins_nl_processor
    - skins_sa_processor
    """

    # Vendor → Processor factory function mapping
    PROCESSOR_MAP = {
        "aromateque": "get_aromateque_processor",
        "boxnox": "get_boxnox_processor",
        "cdlc": "get_cdlc_processor",
        "galilu": "get_galilu_processor",
        "liberty": "get_liberty_processor",
        "selfridges": "get_selfridges_processor",
        "skins_nl": "get_skins_nl_processor",
        "skins_sa": "get_skins_sa_processor",
    }

    def __init__(self):
        """Initialize vendor router"""
        # Processor instances will be cached here
        self._processor_cache = {}

    def detect_and_route(
        self,
        file_path: str,
        filename: str,
        reseller_id: str,
        bibbi_db: Optional[Any] = None
    ) -> tuple[Optional[str], float, Dict[str, Any], Optional[Any]]:
        """
        Detect vendor and route to processor

        Args:
            file_path: Path to uploaded file
            filename: Original filename
            reseller_id: Reseller UUID from database
            bibbi_db: BIBBI database client (for Galilu)

        Returns:
            Tuple of (vendor_name, confidence, metadata, processor_instance)
            Returns (None, 0.0, {}, None) if vendor cannot be detected

        Example:
            vendor, confidence, metadata, processor = router.detect_and_route(
                "/tmp/liberty_sales.xlsx",
                "liberty_sales.xlsx",
                reseller_id="abc-123",
                bibbi_db=db_client
            )

            if processor:
                result = processor.process(file_path, batch_id)
        """
        # Detect vendor
        vendor_name, confidence, metadata = detect_bibbi_vendor(file_path, filename)

        if vendor_name is None or confidence < 0.5:
            return None, 0.0, {}, None

        # Get processor for vendor
        processor = self._get_processor(vendor_name, reseller_id, bibbi_db)

        return vendor_name, confidence, metadata, processor

    def _get_processor(self, vendor_name: str, reseller_id: str, bibbi_db: Optional[Any] = None) -> Optional[Any]:
        """
        Get processor instance for vendor

        Args:
            vendor_name: Detected vendor name
            reseller_id: Reseller UUID
            bibbi_db: BIBBI database client (for Galilu product lookups)

        Returns:
            Processor instance or None if not found
        """
        factory_name = self.PROCESSOR_MAP.get(vendor_name)

        if factory_name is None:
            print(f"[BibbιVendorRouter] No processor mapping for vendor: {vendor_name}")
            return None

        # Check cache (keyed by vendor_name + reseller_id)
        cache_key = f"{vendor_name}:{reseller_id}"
        if cache_key in self._processor_cache:
            return self._processor_cache[cache_key]

        try:
            from app.services.bibbi.processors import (
                get_aromateque_processor,
                get_boxnox_processor,
                get_cdlc_processor,
                get_galilu_processor,
                get_liberty_processor,
                get_selfridges_processor,
                get_skins_nl_processor,
                get_skins_sa_processor
            )

            factory_functions = {
                "get_aromateque_processor": get_aromateque_processor,
                "get_boxnox_processor": get_boxnox_processor,
                "get_cdlc_processor": get_cdlc_processor,
                "get_galilu_processor": get_galilu_processor,
                "get_liberty_processor": get_liberty_processor,
                "get_selfridges_processor": get_selfridges_processor,
                "get_skins_nl_processor": get_skins_nl_processor,
                "get_skins_sa_processor": get_skins_sa_processor,
            }

            factory = factory_functions.get(factory_name)
            if factory:
                # Special case: Galilu needs database client
                if vendor_name == "galilu" and bibbi_db:
                    processor_instance = factory(reseller_id, bibbi_db)
                else:
                    processor_instance = factory(reseller_id)

                self._processor_cache[cache_key] = processor_instance
                return processor_instance

            return None

        except ImportError as e:
            print(f"[BibbιVendorRouter] Failed to import processor: {e}")
            return None

    def get_supported_vendors(self) -> list[str]:
        """
        Get list of supported vendor names

        Returns:
            List of vendor names that can be processed
        """
        return list(self.PROCESSOR_MAP.keys())

    def is_vendor_supported(self, vendor_name: str) -> bool:
        """
        Check if vendor is supported

        Args:
            vendor_name: Vendor name to check

        Returns:
            True if vendor has a processor mapping
        """
        return vendor_name in self.PROCESSOR_MAP


# Global router instance
bibbi_vendor_router = BibbιVendorRouter()


def route_bibbi_vendor(
    file_path: str,
    filename: str,
    reseller_id: str,
    bibbi_db: Optional[Any] = None
) -> tuple[Optional[str], float, Dict[str, Any], Optional[Any]]:
    """
    Convenience function for BIBBI vendor routing

    Args:
        file_path: Path to uploaded file
        filename: Original filename
        reseller_id: Reseller UUID
        bibbi_db: BIBBI database client

    Returns:
        Tuple of (vendor_name, confidence, metadata, processor)
    """
    return bibbi_vendor_router.detect_and_route(file_path, filename, reseller_id, bibbi_db)
